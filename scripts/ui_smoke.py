"""UI-Smoke-Test im Browser-Mock (ohne Tauri).

Start:  python3 scripts/ui_smoke.py [ausgabeordner]
Startet einen HTTP-Server im Repo-Root, klickt die Hauptpfade durch und
speichert Screenshots. Bricht bei JavaScript-Fehlern mit Exit-Code 1 ab.
"""
import http.server
import sys
import threading
from functools import partial
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/lk-shots")
OUT.mkdir(parents=True, exist_ok=True)

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


handler = partial(Quiet, directory=str(ROOT))
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_port}/ui/index.html"

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 400, "height": 860}, device_scale_factor=2, has_touch=True)
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and errors.append(m.text))

    def shot(name):
        pg.wait_for_timeout(500)
        pg.screenshot(path=str(OUT / f"{name}.png"))

    pg.goto(base)
    pg.wait_for_selector(".deck")
    shot("01-home")
    pg.click(".deck >> nth=0")
    pg.wait_for_selector(".item")
    shot("02-deck")
    pg.click(".item >> nth=0")
    shot("03-cardsheet")
    pg.click("#sheet", position={"x": 10, "y": 10})
    pg.click("#learn")
    pg.click("#go")
    pg.wait_for_selector("#card")
    shot("04-study-front")
    pg.click("[data-t=mark]")
    w = pg.locator(".face.front .w").nth(1).bounding_box()
    pg.mouse.move(w["x"] + 3, w["y"] + 5)
    pg.mouse.down()
    pg.mouse.move(w["x"] + 60, w["y"] + 5, steps=5)
    pg.mouse.up()
    pg.click("[data-t=pen]")
    box = pg.locator(".face.front .inkcanvas").bounding_box()
    pg.mouse.move(box["x"] + 40, box["y"] + 80)
    pg.mouse.down()
    pg.mouse.move(box["x"] + 200, box["y"] + 140, steps=8)
    pg.mouse.up()
    shot("05-study-ink")
    pg.click("[data-t=none]")
    pg.click("#flipb")
    shot("06-study-back")
    pg.click("[data-r=kann]")
    pg.wait_for_timeout(300)
    marks = pg.evaluate("JSON.parse(localStorage.getItem('lk-mock')).decks.flatMap(d=>d.cards).filter(c=>c.ink_front&&(c.ink_front.marks.length||c.ink_front.strokes.length)).length")
    assert marks >= 1, "Markierung/Stift wurde nicht gespeichert"
    pg.click("#quit")
    shot("07-done")
    pg.goto(base + "#/edit")
    pg.wait_for_selector("#front")
    pg.fill("#front", "Testfrage ==wichtig==")
    pg.fill("#back", "Antwort mit `code`\n- Punkt 1\n- Punkt 2")
    shot("08-edit")
    pg.click("#prev")
    shot("09-preview")
    pg.goto(base + "#/import")
    pg.wait_for_selector("#use")
    shot("10-import")
    pg.goto(base + "#/search?q=JOIN")
    pg.wait_for_selector(".item")
    shot("11-search")
    pg.goto(base + "#/info")
    shot("12-info")
    b.close()

srv.shutdown()
if errors:
    print("JS-Fehler:", *errors, sep="\n  ")
    sys.exit(1)
print(f"OK – Screenshots in {OUT}")
