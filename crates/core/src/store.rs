//! Laden/Speichern der Bibliothek, Standard-Inhalte einspielen, Bearbeitungsoperationen.
use crate::model::{hash_id, slug, Card, Deck, Ink, Library, Rating};
use crate::schedule::{self, Counts};
use serde::{Deserialize, Serialize};
use std::path::Path;

include!(concat!(env!("OUT_DIR"), "/builtin.rs"));

/// Liest die Bibliothek; fehlt die Datei, wird eine leere angelegt.
pub fn load(path: &Path) -> std::io::Result<Library> {
    match std::fs::read_to_string(path) {
        Ok(s) => serde_json::from_str(&s)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e)),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(Library {
            version: Library::VERSION,
            ..Default::default()
        }),
        Err(e) => Err(e),
    }
}

/// Atomar speichern (tmp + rename), vorherige Version bleibt als `.bak`.
pub fn save(path: &Path, lib: &Library) -> std::io::Result<()> {
    if let Some(dir) = path.parent() {
        std::fs::create_dir_all(dir)?;
    }
    let tmp = path.with_extension("json.tmp");
    std::fs::write(
        &tmp,
        serde_json::to_vec(lib).map_err(std::io::Error::other)?,
    )?;
    if path.exists() {
        let _ = std::fs::copy(path, path.with_extension("json.bak"));
    }
    std::fs::rename(tmp, path)
}

/// Alle eingebetteten Standard-Decks (IDs stabil aus Deck-ID + Vorderseite).
pub fn builtin_decks() -> Vec<Deck> {
    BUILTIN_DECKS
        .iter()
        .map(|(file, json)| {
            let mut d: Deck =
                serde_json::from_str(json).unwrap_or_else(|e| panic!("content/decks/{file}: {e}"));
            if d.id.is_empty() {
                d.id = slug(file.trim_end_matches(".json"));
            }
            d.builtin = true;
            for c in &mut d.cards {
                if c.id.is_empty() {
                    c.id = hash_id("b", &[&d.id, &c.front]);
                }
                c.builtin = true;
            }
            d
        })
        .collect()
}

#[derive(Serialize, Debug, Default, PartialEq)]
pub struct MergeReport {
    pub decks_added: usize,
    pub cards_added: usize,
    pub cards_updated: usize,
    pub cards_removed: usize,
}

/// Spielt Standard-Inhalte ein, ohne Lernfortschritt/Markierungen/eigene Änderungen zu verlieren.
pub fn merge_builtin(lib: &mut Library, restore_hidden: bool) -> MergeReport {
    let mut r = MergeReport::default();
    if restore_hidden {
        lib.settings.hidden_builtin.clear();
    }
    for b in builtin_decks() {
        if lib.settings.hidden_builtin.contains(&b.id) {
            continue;
        }
        let Some(d) = lib.deck_mut(&b.id) else {
            r.decks_added += 1;
            r.cards_added += b.cards.len();
            lib.decks.push(b);
            continue;
        };
        d.name = b.name;
        d.category = b.category;
        d.description = b.description;
        d.color = b.color;
        d.icon = b.icon;
        let before = d.cards.len();
        d.cards
            .retain(|c| !c.builtin || c.edited || b.cards.iter().any(|n| n.id == c.id));
        r.cards_removed += before - d.cards.len();
        for n in b.cards {
            match d.cards.iter_mut().find(|c| c.id == n.id) {
                Some(c) if !c.edited => {
                    if c.back != n.back || c.tags != n.tags || c.prio != n.prio {
                        if c.back != n.back {
                            c.ink_back = Ink::default();
                        }
                        c.back = n.back;
                        c.tags = n.tags;
                        c.prio = n.prio;
                        r.cards_updated += 1;
                    }
                }
                Some(_) => {}
                None => {
                    d.cards.push(n);
                    r.cards_added += 1;
                }
            }
        }
    }
    lib.version = Library::VERSION;
    r
}

/// Fügt importierte Decks hinzu (oder hängt an `target` an). Liefert Anzahl Karten.
pub fn add_imported(
    lib: &mut Library,
    decks: Vec<Deck>,
    target: Option<&str>,
    category: &str,
    now: i64,
) -> Result<usize, String> {
    let mut n = 0;
    for (i, mut d) in decks.into_iter().enumerate() {
        for (j, c) in d.cards.iter_mut().enumerate() {
            c.id = hash_id(
                "u",
                &[&c.front, &now.to_string(), &i.to_string(), &j.to_string()],
            );
            c.builtin = false;
            c.edited = false;
            if c.progress.rating == Rating::New {
                c.progress = Default::default();
            }
        }
        n += d.cards.len();
        if let Some(t) = target.filter(|t| !t.is_empty()) {
            lib.deck_mut(t)
                .ok_or("Ziel-Deck nicht gefunden")?
                .cards
                .append(&mut d.cards);
            continue;
        }
        d.builtin = false;
        if d.category.trim().is_empty() {
            d.category = if category.trim().is_empty() {
                "Eigene Karten".into()
            } else {
                category.into()
            };
        }
        d.id = unique_deck_id(lib, &d.name);
        if d.color.is_empty() {
            d.color = "#7c5cff".into();
        }
        lib.decks.push(d);
    }
    Ok(n)
}

fn unique_deck_id(lib: &Library, name: &str) -> String {
    let base = format!("u-{}", slug(name));
    let mut id = base.clone();
    let mut i = 2;
    while lib.deck(&id).is_some() {
        id = format!("{base}-{i}");
        i += 1;
    }
    id
}

#[derive(Deserialize, Debug, Default)]
#[serde(default)]
pub struct DeckInput {
    pub id: Option<String>,
    pub name: String,
    pub category: String,
    pub description: String,
    pub color: String,
    pub icon: String,
}

pub fn upsert_deck(lib: &mut Library, inp: DeckInput) -> Result<String, String> {
    if inp.name.trim().is_empty() {
        return Err("Name fehlt".into());
    }
    let id = match inp.id.filter(|s| !s.is_empty()) {
        Some(id) => id,
        None => {
            let id = unique_deck_id(lib, &inp.name);
            lib.decks.push(Deck {
                id: id.clone(),
                ..Default::default()
            });
            id
        }
    };
    let d = lib.deck_mut(&id).ok_or("Deck nicht gefunden")?;
    d.name = inp.name.trim().into();
    d.category = if inp.category.trim().is_empty() {
        "Eigene Karten".into()
    } else {
        inp.category.trim().into()
    };
    d.description = inp.description;
    d.color = if inp.color.is_empty() {
        "#7c5cff".into()
    } else {
        inp.color
    };
    d.icon = inp.icon;
    Ok(id)
}

pub fn delete_deck(lib: &mut Library, id: &str) {
    if let Some(d) = lib.deck(id) {
        if d.builtin && !lib.settings.hidden_builtin.iter().any(|h| h == id) {
            lib.settings.hidden_builtin.push(id.into());
        }
    }
    lib.decks.retain(|d| d.id != id);
}

#[derive(Deserialize, Debug, Default)]
#[serde(default)]
pub struct CardInput {
    pub id: Option<String>,
    pub front: String,
    pub back: String,
    pub tags: Vec<String>,
    pub prio: u8,
    pub image: Option<String>,
}

pub fn upsert_card(
    lib: &mut Library,
    deck: &str,
    inp: CardInput,
    now: i64,
) -> Result<Card, String> {
    if inp.front.trim().is_empty() {
        return Err("Vorderseite fehlt".into());
    }
    let d = lib.deck_mut(deck).ok_or("Deck nicht gefunden")?;
    let id = inp.id.filter(|s| !s.is_empty()).unwrap_or_else(|| {
        hash_id(
            "u",
            &[&inp.front, &now.to_string(), &d.cards.len().to_string()],
        )
    });
    let idx = match d.cards.iter().position(|c| c.id == id) {
        Some(i) => i,
        None => {
            d.cards.push(Card {
                id: id.clone(),
                ..Default::default()
            });
            d.cards.len() - 1
        }
    };
    let c = &mut d.cards[idx];
    if c.front != inp.front {
        c.ink_front = Ink::default();
    }
    if c.back != inp.back {
        c.ink_back = Ink::default();
    }
    if c.builtin && (c.front != inp.front || c.back != inp.back) {
        c.edited = true;
    }
    c.front = inp.front;
    c.back = inp.back;
    c.tags = inp
        .tags
        .into_iter()
        .map(|t| t.trim().to_string())
        .filter(|t| !t.is_empty())
        .collect();
    c.prio = inp.prio.min(5);
    c.image = inp.image.filter(|s| !s.is_empty());
    Ok(c.clone())
}

pub fn delete_card(lib: &mut Library, deck: &str, card: &str) {
    if let Some(d) = lib.deck_mut(deck) {
        d.cards.retain(|c| c.id != card);
    }
}

pub fn move_card(lib: &mut Library, from: &str, card: &str, to: &str) -> Result<(), String> {
    if lib.deck(to).is_none() {
        return Err("Ziel-Deck nicht gefunden".into());
    }
    let d = lib.deck_mut(from).ok_or("Deck nicht gefunden")?;
    let i = d
        .cards
        .iter()
        .position(|c| c.id == card)
        .ok_or("Karte nicht gefunden")?;
    let c = d.cards.remove(i);
    lib.deck_mut(to).unwrap().cards.push(c);
    Ok(())
}

/// Bewertung im Lernmodus + Tagesserie.
pub fn review(
    lib: &mut Library,
    deck: &str,
    card: &str,
    r: Rating,
    now: i64,
) -> Result<Card, String> {
    let c = lib.card_mut(deck, card).ok_or("Karte nicht gefunden")?;
    schedule::rate(&mut c.progress, r, now);
    let out = c.clone();
    let day = schedule::today(now);
    let s = &mut lib.settings;
    if s.streak_day != day {
        s.streak = if s.streak_day == day - 1 {
            s.streak + 1
        } else {
            1
        };
        s.streak_day = day;
        s.reviews_today = 0;
    }
    s.reviews_today += 1;
    Ok(out)
}

pub fn reset_progress(lib: &mut Library, deck: Option<&str>) {
    for d in lib
        .decks
        .iter_mut()
        .filter(|d| deck.is_none_or(|id| d.id == id))
    {
        for c in &mut d.cards {
            c.progress = Default::default();
        }
    }
}

#[derive(Serialize, Debug)]
pub struct DeckSummary {
    pub id: String,
    pub name: String,
    pub category: String,
    pub description: String,
    pub color: String,
    pub icon: String,
    pub builtin: bool,
    pub counts: Counts,
}

#[derive(Serialize, Debug)]
pub struct Overview {
    pub decks: Vec<DeckSummary>,
    pub totals: Counts,
    pub streak: u32,
    pub reviews_today: u32,
}

pub fn overview(lib: &Library, now: i64) -> Overview {
    let day = schedule::today(now);
    let mut totals = Counts::default();
    let decks = lib
        .decks
        .iter()
        .map(|d| {
            let counts = Counts::of(d, day);
            totals.add(&counts);
            DeckSummary {
                id: d.id.clone(),
                name: d.name.clone(),
                category: d.category.clone(),
                description: d.description.clone(),
                color: d.color.clone(),
                icon: d.icon.clone(),
                builtin: d.builtin,
                counts,
            }
        })
        .collect();
    let active = lib.settings.streak_day >= day - 1;
    Overview {
        decks,
        totals,
        streak: if active { lib.settings.streak } else { 0 },
        reviews_today: if lib.settings.streak_day == day {
            lib.settings.reviews_today
        } else {
            0
        },
    }
}

/// Volltextsuche (Groß/Klein egal) über Vorder-/Rückseite und Tags.
pub fn search(lib: &Library, q: &str, limit: usize) -> Vec<schedule::StudyCard> {
    let q = q.trim().to_lowercase();
    if q.is_empty() {
        return vec![];
    }
    let mut out = vec![];
    for d in &lib.decks {
        for c in &d.cards {
            let hit = c.front.to_lowercase().contains(&q)
                || c.back.to_lowercase().contains(&q)
                || c.tags.iter().any(|t| t.to_lowercase().contains(&q));
            if hit {
                out.push(schedule::StudyCard {
                    deck_id: d.id.clone(),
                    deck_name: d.name.clone(),
                    color: d.color.clone(),
                    card: c.clone(),
                });
                if out.len() >= limit {
                    return out;
                }
            }
        }
    }
    out
}

/// Export als JSON (wieder importierbar). `with_progress=false` liefert reine Inhalte.
pub fn export(lib: &Library, decks: &[String], with_progress: bool) -> String {
    let mut sel: Vec<Deck> = lib
        .decks
        .iter()
        .filter(|d| decks.is_empty() || decks.contains(&d.id))
        .cloned()
        .collect();
    if !with_progress {
        for d in &mut sel {
            for c in &mut d.cards {
                c.progress = Default::default();
                c.ink_front = Ink::default();
                c.ink_back = Ink::default();
                c.flagged = false;
            }
        }
    }
    serde_json::to_string_pretty(
        &serde_json::json!({ "format": "lernkartei", "version": Library::VERSION, "decks": sel }),
    )
    .unwrap()
}
