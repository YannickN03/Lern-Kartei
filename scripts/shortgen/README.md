# Shorts-Generator

Erzeugt Lern-Shorts im Stil der NotebookLM-„Kurz“-Videos (720×1280, Papierhintergrund, Diagramme, Handschrift-Untertitel) – für Themen, wenn NotebookLM nicht verfügbar ist.

```bash
sudo apt-get install -y libttspico-utils ffmpeg   # Sprachausgabe (SVOX Pico, Deutsch)
pip install pillow
cd scripts/shortgen && python3 v07_groupby.py ../../ui/shorts/07-sql-group-by-having.mp4
```

- `engine.py`: Elemente (Box, Tabelle, Pfeil, Code, Raute, Knoten …), Einblenden, Untertitel, Rendern mit ffmpeg
- `vNN_*.py`: ein Video je Datei; jedes Segment hat `say` (Sprechertext, Fachbegriffe lautschriftlich), `cap` (Untertitel) und `do` (Bildoperationen)
- Schriften: Patrick Hand, Nunito (SIL Open Font License)
