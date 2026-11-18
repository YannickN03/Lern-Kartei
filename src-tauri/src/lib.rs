//! Tauri-Schicht: dünne Commands über `lernkartei-core`. Jede Änderung wird sofort gespeichert.
use lernkartei_core::{
    import,
    schedule::{self, Mode, StudyCard},
    shorts::{self, Feed, Filter, Short},
    store::{self, CardInput, DeckInput, MergeReport, Overview},
    Card, Deck, Ink, Library, Rating,
};
use serde::Serialize;
use std::{path::PathBuf, sync::Mutex};
use tauri::{Manager, State};

struct App {
    lib: Library,
    path: PathBuf,
    shorts: Vec<Short>,
}

type S<'a> = State<'a, Mutex<App>>;
type R<T> = Result<T, String>;

fn now() -> i64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs() as i64)
        .unwrap_or(0)
}

/// Führt `f` aus und speichert danach.
fn mutate<T>(s: &S, f: impl FnOnce(&mut Library) -> R<T>) -> R<T> {
    let mut app = s.lock().map_err(|e| e.to_string())?;
    let out = f(&mut app.lib)?;
    store::save(&app.path, &app.lib).map_err(|e| format!("Speichern fehlgeschlagen: {e}"))?;
    Ok(out)
}

fn read<T>(s: &S, f: impl FnOnce(&Library) -> T) -> R<T> {
    Ok(f(&s.lock().map_err(|e| e.to_string())?.lib))
}

/// Wie `mutate`, aber mit Zugriff auf den Shorts-Katalog.
fn mutate_shorts<T>(s: &S, f: impl FnOnce(&mut Library, &[Short]) -> R<T>) -> R<T> {
    let mut app = s.lock().map_err(|e| e.to_string())?;
    let App { lib, path, shorts } = &mut *app;
    let out = f(lib, shorts)?;
    store::save(path, lib).map_err(|e| format!("Speichern fehlgeschlagen: {e}"))?;
    Ok(out)
}

#[tauri::command]
fn overview(s: S) -> R<Overview> {
    read(&s, |l| store::overview(l, now()))
}

#[tauri::command]
fn deck(s: S, id: String) -> R<Deck> {
    read(&s, |l| l.deck(&id).cloned())?.ok_or_else(|| "Deck nicht gefunden".into())
}

#[tauri::command]
fn study(s: S, decks: Vec<String>, mode: Mode, limit: usize, shuffle: bool) -> R<Vec<StudyCard>> {
    let seed = shuffle.then(|| now() as u64 ^ 0x9e37_79b9_7f4a_7c15);
    read(&s, |l| schedule::queue(l, &decks, mode, limit, seed, now()))
}

#[tauri::command]
fn rate(s: S, deck: String, card: String, rating: Rating) -> R<Card> {
    mutate(&s, |l| store::review(l, &deck, &card, rating, now()))
}

#[tauri::command]
fn sort_card(s: S, deck: String, card: String, rating: Rating) -> R<Card> {
    mutate(&s, |l| {
        let c = l.card_mut(&deck, &card).ok_or("Karte nicht gefunden")?;
        schedule::sort_into(&mut c.progress, rating, now());
        Ok(c.clone())
    })
}

#[tauri::command]
fn set_ink(s: S, deck: String, card: String, side: String, ink: Ink) -> R<()> {
    mutate(&s, |l| {
        let c = l.card_mut(&deck, &card).ok_or("Karte nicht gefunden")?;
        if side == "back" {
            c.ink_back = ink
        } else {
            c.ink_front = ink
        }
        Ok(())
    })
}

#[tauri::command]
fn toggle_flag(s: S, deck: String, card: String) -> R<bool> {
    mutate(&s, |l| {
        let c = l.card_mut(&deck, &card).ok_or("Karte nicht gefunden")?;
        c.flagged = !c.flagged;
        Ok(c.flagged)
    })
}

#[tauri::command]
fn upsert_card(s: S, deck: String, card: CardInput) -> R<Card> {
    mutate(&s, |l| store::upsert_card(l, &deck, card, now()))
}

#[tauri::command]
fn delete_card(s: S, deck: String, card: String) -> R<()> {
    mutate(&s, |l| {
        store::delete_card(l, &deck, &card);
        Ok(())
    })
}

#[tauri::command]
fn move_card(s: S, from: String, card: String, to: String) -> R<()> {
    mutate(&s, |l| store::move_card(l, &from, &card, &to))
}

#[tauri::command]
fn upsert_deck(s: S, deck: DeckInput) -> R<String> {
    mutate(&s, |l| store::upsert_deck(l, deck))
}

#[tauri::command]
fn delete_deck(s: S, id: String) -> R<()> {
    mutate(&s, |l| {
        store::delete_deck(l, &id);
        Ok(())
    })
}

#[derive(Serialize)]
struct ImportReport {
    cards: usize,
    decks: Vec<String>,
}

#[tauri::command]
fn import_text(
    s: S,
    file_name: String,
    content: String,
    deck_name: String,
    category: String,
    target: Option<String>,
) -> R<ImportReport> {
    let fallback = if deck_name.trim().is_empty() {
        file_name
            .rsplit(['/', '\\'])
            .next()
            .unwrap_or("Import")
            .split('.')
            .next()
            .unwrap_or("Import")
            .to_string()
    } else {
        deck_name.trim().to_string()
    };
    let decks = import::parse(&file_name, &content, &fallback).map_err(|e| e.to_string())?;
    let names = decks.iter().map(|d| d.name.clone()).collect();
    let cards = mutate(&s, |l| {
        store::add_imported(l, decks, target.as_deref(), &category, now())
    })?;
    Ok(ImportReport {
        cards,
        decks: names,
    })
}

#[tauri::command]
fn export_json(s: S, decks: Vec<String>, with_progress: bool) -> R<String> {
    read(&s, |l| store::export(l, &decks, with_progress))
}

#[tauri::command]
fn search(s: S, query: String) -> R<Vec<StudyCard>> {
    read(&s, |l| store::search(l, &query, 200))
}

#[tauri::command]
fn reset_progress(s: S, deck: Option<String>) -> R<()> {
    mutate(&s, |l| {
        store::reset_progress(l, deck.as_deref());
        Ok(())
    })
}

#[tauri::command]
fn restore_builtin(s: S) -> R<MergeReport> {
    mutate(&s, |l| Ok(store::merge_builtin(l, true)))
}

#[tauri::command]
fn shorts_feed(s: S, filter: Filter, deck: Option<String>, shuffle: bool) -> R<Feed> {
    let app = s.lock().map_err(|e| e.to_string())?;
    let seed = shuffle.then(|| now() as u64 ^ 0x2545_f491_4f6c_dd1d);
    Ok(shorts::feed(
        &app.lib,
        &app.shorts,
        filter,
        deck.as_deref(),
        seed,
    ))
}

#[tauri::command]
fn short_seen(s: S, id: String) -> R<()> {
    mutate_shorts(&s, |l, c| shorts::mark_seen(l, c, &id, now()))
}

#[tauri::command]
fn short_like(s: S, id: String) -> R<bool> {
    mutate_shorts(&s, |l, c| shorts::toggle_like(l, c, &id))
}

#[tauri::command]
fn shorts_reset(s: S) -> R<()> {
    mutate(&s, |l| {
        shorts::reset_seen(l);
        Ok(())
    })
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .setup(|app| {
            let dir = app.path().app_data_dir()?;
            let path = dir.join("library.json");
            let mut lib = store::load(&path)
                .or_else(|_| store::load(&path.with_extension("json.bak")))
                .unwrap_or_default();
            store::merge_builtin(&mut lib, false);
            store::save(&path, &lib)?;
            app.manage(Mutex::new(App {
                lib,
                path,
                shorts: shorts::catalog(),
            }));
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            overview,
            deck,
            study,
            rate,
            sort_card,
            set_ink,
            toggle_flag,
            upsert_card,
            delete_card,
            move_card,
            upsert_deck,
            delete_deck,
            import_text,
            export_json,
            search,
            reset_progress,
            restore_builtin,
            shorts_feed,
            short_seen,
            short_like,
            shorts_reset
        ])
        .run(tauri::generate_context!())
        .expect("Fehler beim Starten von LernKartei");
}
