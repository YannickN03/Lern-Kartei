# Shorts-Generator

Erzeugt Lern-Shorts im Stil der NotebookLM-„Kurz“-Videos (720×1280, Papierhintergrund, Diagramme, Handschrift-Untertitel) – für Themen, wenn NotebookLM nicht verfügbar ist.

```bash
sudo apt-get install -y libttspico-utils ffmpeg   # Sprachausgabe (SVOX Pico, Deutsch)
pip install pillow
cd scripts/shortgen && python3 v07_groupby.py ../../ui/shorts/07-sql-group-by-having.mp4
```

**Mit Gemini-Stimme (empfohlen):** In Google AI Studio → *Generate speech* (Stimme „Lumi“, Stil-Anweisung siehe unten) den Text aus `python3 narration.py 07` einfügen (Szenen sind durch `<long pause>` getrennt), WAV herunterladen und angeben:

```bash
python3 v07_groupby.py ../../ui/shorts/07-sql-group-by-having.mp4 gemini-07.wav
```

Der Generator ordnet die Szenen über Silbenzahl + Sprechpausen der Sprachspur zu. Ohne WAV wird offline mit SVOX Pico vertont.

Stil-Anweisung: *Deutsche Erklärstimme für ein kurzes Lernvideo für Azubis vor der IHK-Abschlussprüfung. Muttersprachliches Hochdeutsch, warm, freundlich und selbstsicher wie ein guter Tutor, lebendig aber nicht werblich. Zügiges, natürliches Tempo (ca. 155 Wörter/Minute), klare Betonung der Fachbegriffe, kurze Pausen nach jedem Satz. Englische Fachbegriffe korrekt englisch aussprechen, Abkürzungen (SQL, UML, AES …) buchstabieren.*

- `narration.py`: Sprechertexte für Gemini (je Szene ein Eintrag)
- `engine.py`: Elemente (Box, Tabelle, Pfeil, Code, Raute, Knoten …), Einblenden, Untertitel, Rendern mit ffmpeg
- `vNN_*.py`: ein Video je Datei; jedes Segment hat `say` (Sprechertext, Fachbegriffe lautschriftlich), `cap` (Untertitel) und `do` (Bildoperationen)
- Schriften: Patrick Hand, Nunito (SIL Open Font License)
