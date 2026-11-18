# 🗂️ LernKartei

Karteikarten-App für Android – geschrieben in **Rust** (Tauri 2) – vorbefüllt mit **~350 Karten für die AP2 Fachinformatiker/-in Anwendungsentwicklung** (Prüfungskatalog ab 2025).

## 📲 APK herunterladen

**[⬇️ LernKartei.apk (neueste Version)](https://github.com/YannickN03/Lern-Kartei/releases/latest/download/LernKartei.apk)** · [alle Versionen](https://github.com/YannickN03/Lern-Kartei/releases)

APK auf dem Handy öffnen → „Installation aus unbekannten Quellen“ erlauben → installieren. Neue Versionen einfach drüber installieren, der Lernfortschritt bleibt erhalten.

## Funktionen
- Karten **umdrehen** (Tippen) und **einsortieren**: ✓ *Kann ich* · ~ *Geht so* · ✗ *Nicht* – auch per Wischen
- **Leitner-System**: Wiederholung nach 1 / 3 / 7 / 14 / 30 Tagen
- **Markieren** (3 Textmarker-Farben) und **Stift/Radierer** direkt auf der Karte
- **Lernkategorien** und Decks, eigene Karten mit Code, Tabellen, Listen und **Bildern**
- **Import** von JSON, CSV/TSV, Text, Markdown · **Export/Backup** als JSON · JSON-Vorlage für neue Karten
- Lernmodi: fällig, alle, Schwächen, neue, gemerkte ⭐ – gemischt oder sortiert
- Suche, Tagesserie, Prüfungsinfo, komplett offline

## Inhalte (AP2 FIAE)
| Kategorie | Themen |
|---|---|
| Planen eines Softwareproduktes | UML (Klassen-, Aktivitäts-, Sequenz-, Zustands-, Use-Case-Diagramm), BPMN 2.0, OOP & Patterns, Vorgehensmodelle & Scrum, Netzplan, Nutzwert/Amortisation, QS & Testen, REST/HTTP, KI, Container |
| Entwicklung & Algorithmen | SQL (DDL/DML, JOINs, GROUP BY, Subqueries), ERM & Normalisierung, NoSQL, Pseudocode, Sortier-/Suchalgorithmen, Rekursion, Datenstrukturen |
| IT-Sicherheit & Infrastruktur | Schutzziele, OWASP/SQL-Injection/XSS, Kryptografie, Backup, RAID, OSI, Subnetting, VPN/VLAN |
| WiSo | Ausbildung, Arbeitsrecht, Mitbestimmung, Sozialversicherung, Verträge, Rechtsformen, Nachhaltigkeit, DSGVO, Lizenzen, Kalkulation |
| Projekt & Präsentation | Projektantrag, Doku, Präsentation, Fachgespräch |
| AP1 → AP2 | Rechenaufgaben und Grundlagen aus AP1, die in AP2 wiederkommen |

Struktur und Priorisierung orientieren sich an [ap2-fiae.de](https://www.ap2-fiae.de/). Angaben ohne Gewähr – maßgeblich ist der offizielle Prüfungskatalog. Format für eigene Karten: [`content/README.md`](content/README.md).

## Entwicklung
```bash
cargo test -p lernkartei-core          # Logik + Validierung aller Inhalte
python3 scripts/ui_smoke.py /tmp/shots # UI im Browser-Mock durchklicken (Playwright)
python3 -m http.server                 # → http://localhost:8000/ui/  (Browser-Vorschau)
```
Konzept & Architektur: [`docs/KONZEPT.md`](docs/KONZEPT.md) · Agent-Hinweise: [`CLAUDE.md`](CLAUDE.md)

**Signatur:** Die CI signiert mit `keystore/lernkartei.jks` (öffentlich, für privates Sideloading gedacht). Für eine Veröffentlichung im Play Store eigene Secrets `ANDROID_KEYSTORE_B64` / `ANDROID_KEYSTORE_PASSWORD` (Alias `lernkartei`) setzen – danach einmal neu installieren.

Lizenz: MIT
