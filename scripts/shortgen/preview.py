"""Vorschau: Endzustand jeder Szene als PNG (ohne Audio), z. B. python3 preview.py v17_binaere_suche /tmp/prev"""
import importlib, os, sys
from engine import *

mod = importlib.import_module(sys.argv[1])
out = sys.argv[2]
os.makedirs(out, exist_ok=True)
bg = paper()
state, order = {}, []
for si, seg in enumerate(mod.SEG):
    for op in seg.get('do', []):
        if op[0] == 'add':
            state[op[1]] = [op[2], None]
            if op[1] in order: order.remove(op[1])
            order.append(op[1])
        elif op[0] == 'rm':
            for k in op[1:]:
                state.pop(k, None)
                if k in order: order.remove(k)
        elif op[0] == 'clear':
            state.clear(); order.clear()
        elif op[0] == 'hl':
            state[op[1]][1] = op[2]
    img = bg.copy(); d = ImageDraw.Draw(img)
    for i in order:
        el, hl = state[i]; el.draw(d, img, hl)
    chunks = caption_chunks(seg.get('cap', seg['say']))
    draw_caption(img, chunks[0])
    img.resize((W // 2, H // 2), Image.LANCZOS).save(f'{out}/{si:02d}.png')
