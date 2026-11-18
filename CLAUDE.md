# LernKartei – Arbeitskarte für Agents

Karteikarten-App (Android-APK) in **Rust + Tauri 2**, UI in Vanilla-JS ohne Build-Schritt. Vorbefüllt mit AP2-FIAE-Inhalten.

## Wo liegt was (erst hier nachsehen, nicht das Repo durchsuchen)
| Pfad | Inhalt |
|---|---|
| `crates/core/src/model.rs` | Datenmodell: Library → Deck → Card (Progress, Ink) |
| `crates/core/src/schedule.rs` | Leitner (Fächer 0–5, Intervalle 0/1/3/7/14/30), Lernstapel, Zähler |
| `crates/core/src/import.rs` | Import JSON / CSV / Text / Markdown |
| `crates/core/src/store.rs` | Laden/Speichern, Standard-Inhalte mergen, CRUD, Suche, Export |
| `crates/core/build.rs` | bettet `content/decks/*.json` automatisch ein |
| `crates/core/tests/core.rs` | alle Tests inkl. Inhaltsvalidierung |
| `src-tauri/src/lib.rs` | Tauri-Commands (dünn, rufen nur `store`/`schedule`) |
| `ui/app.js` | Router + alle Screens; `ui/md.js` Mini-Markdown; `ui/ink.js` Markieren/Stift; `ui/api.js` Tauri-Bridge + Browser-Mock |
| `content/decks/NN-name.json` | Lerninhalte, ein Deck pro Datei (Schema: `content/README.md`) |
| `.github/workflows/android.yml` | APK bauen, signieren, Release |

## Befehle
- Tests: `cargo test -p lernkartei-core` (validiert auch alle Inhalte)
- Lint: `cargo fmt --all && cargo clippy -p lernkartei-core --all-targets -- -D warnings`
- UI im Browser testen: `python3 scripts/ui_smoke.py /tmp/shots` (Screenshots + JS-Fehlerprüfung)
- Manuell: `python3 -m http.server` im Root → `http://localhost:8000/ui/`
- Android lokal: `npm ci && npm run tauri -- android init && npm run tauri -- android build --apk` (SDK/NDK nötig; sonst nur CI)

## Regeln
- Logik gehört in `crates/core` (testbar), nicht in `src-tauri` oder JS.
- Neuer Command: Funktion in `store.rs` + Test → Wrapper in `src-tauri/src/lib.rs` + `generate_handler!` → Aufruf `call('name', {camelCaseArgs})` in `app.js` → Mock in `api.js`.
- Neue Inhalte: Datei in `content/decks/` ablegen; Karten-ID = Hash(Deck-ID + Vorderseite) → Vorderseite ändern = neue Karte (Fortschritt weg), Rückseite ändern = Update mit Fortschritt.
- Inhalte nur nach aktuellem AP2-Katalog (Stand 2025): kein Struktogramm/PAP; AP1-Überschneidungen mit Tag `AP1`.
- Version: `src-tauri/tauri.conf.json` + `Cargo.toml` (workspace). versionCode setzt die CI.
