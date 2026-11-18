//! Lern-Shorts: kurze Hochkant-Videos (z. B. aus NotebookLM), die man wie Reels durchscrollt.
//!
//! Videos liegen in `ui/shorts/` und werden mit der App ausgeliefert. Metadaten (Titel, Deck,
//! Tags) stehen optional in `content/shorts.json`. Eine Videodatei ohne Manifest-Eintrag
//! erscheint trotzdem (Titel aus dem Dateinamen); ein Manifest-Eintrag ohne Datei gilt als
//! „angekündigt“ und wird nicht im Feed gezeigt.
use crate::model::{slug, Library};
use crate::schedule::shuffle;
use crate::store::shorts_sources;
use serde::{Deserialize, Serialize};

/// Ein Short aus Manifest und/oder Videoordner.
#[derive(Serialize, Deserialize, Clone, Debug, PartialEq, Default)]
#[serde(default)]
pub struct Short {
    /// Stabile ID (Standard: Slug des Dateinamens ohne Endung).
    pub id: String,
    /// Dateiname in `ui/shorts/`.
    pub file: String,
    pub title: String,
    pub description: String,
    /// Passendes Deck (Deck-ID) → „Karten dazu lernen“.
    pub deck: String,
    pub tags: Vec<String>,
    /// Videodatei ist in der App enthalten.
    pub available: bool,
}

#[derive(Deserialize, Default)]
struct Manifest {
    #[serde(default)]
    shorts: Vec<Short>,
}

/// Titel aus Dateinamen: „03-pseudocode_arrays.mp4“ → „Pseudocode arrays“.
pub fn title_from_file(file: &str) -> String {
    let stem = file.rsplit_once('.').map_or(file, |(s, _)| s);
    let stem = stem.trim_start_matches(|c: char| c.is_ascii_digit() || c == '-' || c == '_');
    let words = stem.replace(['-', '_'], " ");
    let words = words.split_whitespace().collect::<Vec<_>>().join(" ");
    let mut cs = words.chars();
    match cs.next() {
        Some(f) => f.to_uppercase().chain(cs).collect(),
        None => file.to_string(),
    }
}

/// Manifest + Dateiliste zusammenführen. Reihenfolge: Manifest, danach unbekannte Dateien.
pub fn catalog_from(manifest: &str, files: &[&str]) -> Result<Vec<Short>, String> {
    let m: Manifest = if manifest.trim().is_empty() {
        Manifest::default()
    } else {
        serde_json::from_str(manifest).map_err(|e| format!("content/shorts.json: {e}"))?
    };
    let has = |f: &str| files.iter().any(|x| x.eq_ignore_ascii_case(f));
    let mut out: Vec<Short> = m
        .shorts
        .into_iter()
        .map(|mut s| {
            if s.id.is_empty() {
                s.id = slug(s.file.rsplit_once('.').map_or(&s.file, |(a, _)| a));
            }
            if s.title.is_empty() {
                s.title = title_from_file(&s.file);
            }
            s.available = !s.file.is_empty() && has(&s.file);
            s
        })
        .collect();
    for f in files {
        if out.iter().any(|s| s.file.eq_ignore_ascii_case(f)) {
            continue;
        }
        out.push(Short {
            id: slug(f.rsplit_once('.').map_or(f, |(a, _)| a)),
            file: f.to_string(),
            title: title_from_file(f),
            available: true,
            ..Default::default()
        });
    }
    Ok(out)
}

/// Alle eingebetteten Shorts (angekündigte inklusive).
pub fn catalog() -> Vec<Short> {
    let (m, files) = shorts_sources();
    catalog_from(m, files).unwrap_or_else(|e| panic!("{e}"))
}

#[derive(Serialize, Deserialize, Clone, Copy, Debug, PartialEq, Eq, Default)]
#[serde(rename_all = "lowercase")]
pub enum Filter {
    /// Ungesehene zuerst, danach bereits gesehene.
    #[default]
    All,
    /// Nur noch nicht gesehene.
    New,
    /// Nur gemerkte ❤️
    Liked,
}

/// Eintrag im Feed: Short + Zustand des Nutzers.
#[derive(Serialize, Clone, Debug, PartialEq)]
pub struct FeedItem {
    #[serde(flatten)]
    pub short: Short,
    pub seen: bool,
    pub liked: bool,
    pub views: u32,
    /// Name/Symbol des verknüpften Decks (leer, wenn es das Deck nicht gibt).
    pub deck_name: String,
    pub deck_icon: String,
}

#[derive(Serialize, Debug, Default, PartialEq)]
pub struct Feed {
    pub items: Vec<FeedItem>,
    /// Verfügbare Shorts insgesamt / davon gesehen.
    pub total: usize,
    pub seen: usize,
    /// Angekündigte Shorts ohne Videodatei („Video folgt“).
    pub upcoming: Vec<Short>,
}

/// Baut den Feed. `deck` schränkt auf ein Deck ein, `shuffle_seed` mischt (ungesehene bleiben vorn).
pub fn feed(
    lib: &Library,
    catalog: &[Short],
    filter: Filter,
    deck: Option<&str>,
    shuffle_seed: Option<u64>,
) -> Feed {
    let in_deck = |s: &Short| deck.is_none_or(|d| s.deck == d);
    let mut fd = Feed::default();
    let mut items: Vec<FeedItem> = vec![];
    for s in catalog.iter().filter(|s| in_deck(s)) {
        if !s.available {
            fd.upcoming.push(s.clone());
            continue;
        }
        let st = lib.shorts.get(&s.id).cloned().unwrap_or_default();
        fd.total += 1;
        fd.seen += st.seen as usize;
        let keep = match filter {
            Filter::All => true,
            Filter::New => !st.seen,
            Filter::Liked => st.liked,
        };
        if !keep {
            continue;
        }
        let d = lib.deck(&s.deck);
        items.push(FeedItem {
            short: s.clone(),
            seen: st.seen,
            liked: st.liked,
            views: st.views,
            deck_name: d.map(|d| d.name.clone()).unwrap_or_default(),
            deck_icon: d.map(|d| d.icon.clone()).unwrap_or_default(),
        });
    }
    if let Some(seed) = shuffle_seed {
        shuffle(&mut items, seed);
    }
    // stabil: ungesehene vor gesehenen, sonst Reihenfolge beibehalten
    items.sort_by_key(|i| i.seen);
    fd.items = items;
    fd
}

fn known(catalog: &[Short], id: &str) -> Result<(), String> {
    catalog
        .iter()
        .any(|s| s.id == id)
        .then_some(())
        .ok_or_else(|| "Short nicht gefunden".into())
}

/// Short wurde (fast) komplett angesehen.
pub fn mark_seen(lib: &mut Library, catalog: &[Short], id: &str, now: i64) -> Result<(), String> {
    known(catalog, id)?;
    let st = lib.shorts.entry(id.to_string()).or_default();
    st.seen = true;
    st.views += 1;
    st.last = now;
    Ok(())
}

/// Merken an/aus; liefert den neuen Zustand.
pub fn toggle_like(lib: &mut Library, catalog: &[Short], id: &str) -> Result<bool, String> {
    known(catalog, id)?;
    let st = lib.shorts.entry(id.to_string()).or_default();
    st.liked = !st.liked;
    Ok(st.liked)
}

/// „Gesehen“-Status aller Shorts zurücksetzen (Merkliste bleibt).
pub fn reset_seen(lib: &mut Library) {
    lib.shorts.retain(|_, s| s.liked);
    for s in lib.shorts.values_mut() {
        s.seen = false;
        s.views = 0;
    }
}
