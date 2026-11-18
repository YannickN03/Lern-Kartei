# Inhalte & JSON-Format

Jede Datei in `decks/` ist ein Deck und wird beim Build automatisch in die App eingebettet. Dasselbe Format kann in der App importiert werden (Tab **Import**).

```json
{
  "id": "sql",                    // optional, sonst aus Dateiname
  "name": "SQL",
  "category": "Entwicklung & Algorithmen",   // Lernkategorie (Gruppierung)
  "description": "…",
  "color": "#4cc3ff",
  "icon": "🗄️",
  "cards": [
    { "front": "Frage", "back": "Antwort", "tags": ["SQL", "AP1"], "prio": 5 }
  ]
}
```

- `prio`: 5 essentiell · 4 sehr hoch · 3 hoch · 2 mittel · 1 niedrig (nach Häufigkeit in bisherigen Prüfungen, Orientierung: ap2-fiae.de)
- Tag `AP1`: Thema aus Teil 1, das in AP2 wieder relevant ist. Tag `Übung`: Rechen-/Schreibaufgabe.
- Aliase beim Import: `q`/`a`, `question`/`answer`, `frage`/`antwort`.
- Formatierung: `**fett**`, `==markiert==`, `` `code` ``, Codeblöcke mit ```` ``` ````, Listen (`- `, `1. `), Tabellen (`| a | b |`).

Weitere Importformate: CSV/TSV (`Vorderseite;Rückseite;Tags`), Text (`Frage :: Antwort` je Zeile oder `F:`/`A:`-Blöcke), Markdown (`## Frage` + Antworttext).

## Kategorien (Prüfungsbereiche AP2)
| Kategorie | Decks |
|---|---|
| Planen eines Softwareproduktes | UML & BPMN, OOP & Patterns, Projekt & Vorgehensmodelle, Qualität & Testen, Web & Technologien |
| Entwicklung & Algorithmen | SQL, Datenmodellierung, Algorithmen & Pseudocode |
| IT-Sicherheit & Infrastruktur | IT-Sicherheit & Datenschutz, Netzwerk |
| WiSo | Wirtschafts- und Sozialkunde, Datenschutz/Recht/Kalkulation |
| Projekt & Präsentation | Betriebliche Projektarbeit |
| AP1 → AP2 | Rechen- und Grundlagenthemen aus AP1 |
