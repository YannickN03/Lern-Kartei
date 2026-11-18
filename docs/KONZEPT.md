# Konzept

## Ziel
Offline-Karteikarten-App für Android zum Lernen für die **AP2 Fachinformatiker/-in Anwendungsentwicklung**, mit eigenen Karten, Import und persönlichen Anmerkungen auf den Karten.

## Vorbilder
| App | Übernommen | Bewusst anders |
|---|---|---|
| Anki / AnkiDroid (Open Source) | Spaced Repetition, Decks, Tags, Import/Export | statt 4 Knöpfen und komplexem Algorithmus nur 3 klare Stapel |
| Quizlet | Wisch-Gesten, Flip-Animation, schnelles Erstellen | kein Konto, keine Cloud, keine Werbung |
| Leitner-Kartei (Papier) | Fächer-System, Einsortieren in Stapel | – |
| Brainyoo / Repetico | Bilder auf Karten, Markieren | Markierungen pro Wort statt Freitext-Textmarker |
| ap2-fiae.de | Themenstruktur, 13 Gebiete, Priorisierung nach Prüfungshäufigkeit | als Karteikarten statt Lernseiten |

## Funktionen
- **Karteikarten** mit Vorder-/Rückseite, 3D-Umdrehen per Tipp, Markdown (Code, Tabellen, Listen), Bilder.
- **Einsortieren**: *Kann ich* / *Geht so* / *Nicht* – per Knopf oder Wischen (→ / ↑ / ←), auch manuell aus der Kartenliste.
- **Leitner-System**: Fach 0–5, Wiederholung nach 0/1/3/7/14/30 Tagen; „Nicht“ kommt in derselben Runde noch einmal.
- **Markieren** (3 Textmarker-Farben, Wörter antippen/überstreichen) und **Stift/Radierer** zum Zeichnen auf der Karte; pro Kartenseite gespeichert.
- **Lernkategorien** → Decks → Karten; eigene Kategorien/Decks anlegen, Farben/Symbole.
- **Lernmodi**: Fällig, Alle, Schwächen, Neu, nur Nicht/Geht so/Kann ich, Gemerkte ⭐; mischen, Anzahl begrenzen; Kategorie- oder Gesamtlernen.
- **Import**: JSON/CSV/TSV/TXT/MD per Datei oder Einfügen; **JSON-Vorlage** für neue Karten. **Export** als JSON (mit oder ohne Fortschritt) = Backup.
- **Suche**, Tagesserie, Fortschrittsring, Prüfungsinfo-Seite.
- **Lern-Shorts**: kurze Hochkant-Videos (aus NotebookLM „Video-Zusammenfassung → Kurz“) im Reels-Stil: Wischen zum nächsten Video, Autoplay, Tippen = Pause, Doppeltippen = merken, Tempo 1–2×, Verknüpfung zum passenden Deck. Ungesehene zuerst; „gesehen“ ab 85 % Laufzeit.
  - Videos liegen in `ui/shorts/` und sind Teil der App (offline). Manifest `content/shorts.json` liefert Titel/Deck; Dateien ohne Eintrag erscheinen mit Titel aus dem Dateinamen, Einträge ohne Datei als „Video folgt“.
  - Wiedergabe direkt aus den App-Assets; falls die WebView das nicht kann, Fallback über Blob-URL. Die CI rechnet Videos vor dem Build auf max. 720p/H.264 mit Fast-Start herunter.

## Architektur
```
ui/ (HTML/CSS/JS, kein Build)  ──invoke──▶  src-tauri (Commands)  ──▶  crates/core (Logik, testbar)
                                                                            │
                                               App-Datenordner/library.json ◀┘  (+ .bak)
content/decks/*.json ── build.rs ──▶ in die App eingebettet, beim Start gemerged
```
- **Rust-Kern** ohne UI-Abhängigkeit → komplette Logik mit `cargo test` prüfbar, ohne Android-SDK.
- **Tauri 2** liefert Android-WebView + native Datei-Dialoge (Content-URIs). WebView statt nativer Rust-GUI, weil Texteingabe/Soft-Keyboard und Dateiauswahl auf Android damit zuverlässig funktionieren.
- **Speicherung**: eine JSON-Datei, atomar geschrieben, Vorversion als `.bak`.
- **Inhalts-Updates**: Karten-IDs sind Hashes aus Deck + Vorderseite; neue App-Versionen ergänzen/aktualisieren Standardkarten, ohne Fortschritt, Markierungen oder eigene Änderungen zu überschreiben. Gelöschte Standard-Decks bleiben gelöscht (wiederherstellbar).

## Inhalte
- Grundlage: Prüfungskatalog der AkA (Fassung Okt. 2024, gültig ab 2025) – u. a. Struktogramm/PAP gestrichen, BPMN 2.0, Sortieralgorithmen, KI-Grundlagen und Nachhaltigkeit neu, SQL und RAID von AP1 nach AP2 verschoben.
- Struktur und Priorisierung angelehnt an ap2-fiae.de (Häufigkeit in den letzten Prüfungen).
- AP1-Themen, die in AP2-Aufgaben wiederkehren (Sicherheit, Netzwerk, Wirtschaftlichkeit, Verträge, Rechenaufgaben), mit Tag `AP1` und eigenem Wiederholungsdeck.

## Auslieferung
GitHub Actions baut bei jedem Push auf `main` eine signierte APK (arm64 + armv7) und veröffentlicht sie als Release. Fortlaufender `versionCode` → Updates installieren sich über die bestehende App.
