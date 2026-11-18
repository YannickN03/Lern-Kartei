# Lern-Shorts (Videos)

Hier liegen die Hochkant-Videos für den **Shorts**-Tab der App (z. B. „Video-Zusammenfassung → Kurz“ aus NotebookLM).

1. Video als `.mp4` herunterladen und **hier** ablegen.
2. Am besten so benennen, wie es in [`content/shorts.json`](../../content/shorts.json) steht (z. B. `01-sql-joins.mp4`) – dann bekommt es Titel, Beschreibung und das passende Deck.
3. Committen/hochladen – fertig. Die CI komprimiert die Videos beim APK-Build automatisch (720p, H.264, Fast-Start).

Videos mit anderem Namen erscheinen trotzdem; der Titel wird dann aus dem Dateinamen gebildet.
Neue Themen: Eintrag in `content/shorts.json` ergänzen (`file`, `title`, `description`, `deck` = Deck-ID, `tags`).
