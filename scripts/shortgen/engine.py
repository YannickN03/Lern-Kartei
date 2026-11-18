"""Mini-Engine für Lern-Shorts im NotebookLM-„Kurz“-Stil (720x1280, Papier, dünne Boxen,
Handschrift-Untertitel). Szene = Liste von Segmenten; jedes Segment hat Sprechertext (`say`),
optional Anzeige-Untertitel (`cap`) und Bildoperationen (`do`).
"""
import math, os, random, re, subprocess, wave, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, S = 720, 1280, 2           # logisch, Supersampling-Faktor
FPS = 15
HERE = os.path.dirname(os.path.abspath(__file__))
F = {
    'hand': f'{HERE}/fonts/PatrickHand.ttf',
    'bold': f'{HERE}/fonts/Nunito-Bold.ttf',
    'xbold': f'{HERE}/fonts/Nunito-XBold.ttf',
    'reg': f'{HERE}/fonts/Nunito.ttf',
    'mono': '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
    'monob': '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
}
_fc = {}
def font(kind, size):
    k = (kind, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(F[kind], int(size * S))
    return _fc[k]

BG = (240, 237, 224)
INK = (52, 58, 64)
MUTED = (110, 112, 110)
BLUE = (63, 106, 138); BLUE_F = (232, 240, 244)
GREEN = (98, 146, 84); GREEN_F = (236, 243, 228)
RED = (192, 80, 77); RED_F = (250, 236, 232)
ORANGE = (214, 138, 52); ORANGE_F = (250, 238, 220)
PURPLE = (124, 92, 170); PURPLE_F = (240, 234, 248)
TEAL = (126, 186, 204); TEAL_F = (214, 236, 242)
CARD = (247, 244, 236)
COLORS = {'blue': (BLUE, BLUE_F), 'green': (GREEN, GREEN_F), 'red': (RED, RED_F),
          'orange': (ORANGE, ORANGE_F), 'purple': (PURPLE, PURPLE_F), 'gray': (MUTED, CARD),
          'teal': (BLUE, TEAL_F)}

def s(v): return int(round(v * S))

# ---------- Papierhintergrund ----------
def paper():
    random.seed(7)
    img = Image.new('RGB', (W * S, H * S), BG)
    noise = Image.effect_noise((W * S // 4, H * S // 4), 9).convert('L').resize((W * S, H * S), Image.BICUBIC)
    tint = Image.new('RGB', img.size, (226, 221, 204))
    img = Image.composite(img, tint, noise.point(lambda p: 255 - max(0, p - 118) * 3))
    d = ImageDraw.Draw(img)
    for _ in range(900):  # Fasern
        x, y = random.randrange(W * S), random.randrange(H * S)
        d.point((x, y), fill=(222, 217, 200))
    return img.filter(ImageFilter.GaussianBlur(0.6))

# ---------- Elemente ----------
class El:
    def draw(self, d, img, hl=None): ...

def text_w(t, f):
    b = f.getbbox(t)
    return (b[2] - b[0]) / S

def draw_text(d, x, y, t, f, fill, anchor='mm'):
    d.text((s(x), s(y)), t, font=f, fill=fill, anchor=anchor)

def rrect(d, x, y, w, h, r, outline, fill=None, width=2):
    d.rounded_rectangle((s(x), s(y), s(x + w), s(y + h)), radius=s(r), outline=outline, fill=fill, width=s(width))

class Text(El):
    def __init__(self, x, y, t, size=26, color=INK, kind='bold', anchor='mm'):
        self.a = (x, y, t, size, color, kind, anchor)
    def draw(self, d, img, hl=None):
        x, y, t, size, color, kind, anchor = self.a
        for i, line in enumerate(t.split('\n')):
            draw_text(d, x, y + i * size * 1.3, line, font(kind, size), hl or color, anchor)

class Box(El):
    """Rechteck mit optionalem Titel und Zeilen (UML-Klasse: sections=[[...],[...]])."""
    def __init__(self, x, y, w, h, color='blue', title=None, lines=(), sections=None, size=22,
                 r=8, fill=None, align='mm', title_size=None, mono=False, filled=False, underline=()):
        self.__dict__.update(locals()); del self.__dict__['self']
    def draw(self, d, img, hl=None):
        c, cf = COLORS[self.color]
        if hl: c, cf = COLORS[hl]
        x, y, w, h = self.x, self.y, self.w, self.h
        if self.filled:
            rrect(d, x, y, w, h, self.r, c, c)
            draw_text(d, x + w / 2, y + h / 2, self.title, font('xbold', self.title_size or self.size), (255, 255, 255))
            return
        rrect(d, x, y, w, h, self.r, c, self.fill or cf)
        cy = y
        if self.title:
            ts = self.title_size or self.size + 2
            tl = self.title.split('\n')
            th = ts * (1.9 + 1.25 * (len(tl) - 1))
            for k, tline in enumerate(tl):
                draw_text(d, x + w / 2, y + ts * 0.95 + k * ts * 1.25, tline, font('xbold', ts), INK)
            cy = y + th
            if self.sections or self.lines:
                d.line((s(x), s(cy), s(x + w), s(cy)), fill=c, width=s(2))
        if self.sections:
            for si, sec in enumerate(self.sections):
                sy = cy + 8
                for li, l in enumerate(sec):
                    yy = sy + li * self.size * 1.35 + self.size * 0.6
                    draw_text(d, x + 14, yy, l, font('mono' if self.mono else 'reg', self.size), INK, 'lm')
                    if l in self.underline:
                        tw = text_w(l, font('mono' if self.mono else 'reg', self.size))
                        d.line((s(x + 14), s(yy + self.size * 0.62), s(x + 14 + tw), s(yy + self.size * 0.62)), fill=INK, width=s(1.5))
                cy = sy + len(sec) * self.size * 1.35 + 8
                if si < len(self.sections) - 1:
                    d.line((s(x), s(cy), s(x + w), s(cy)), fill=c, width=s(2))
        elif self.lines:
            n = len(self.lines)
            body = y + h - cy
            for i, l in enumerate(self.lines):
                yy = cy + body * (i + 0.5) / n
                if self.align == 'lm':
                    draw_text(d, x + 16, yy, l, font('mono' if self.mono else 'reg', self.size), INK, 'lm')
                else:
                    draw_text(d, x + w / 2, yy, l, font('mono' if self.mono else 'reg', self.size), INK)

class Table(El):
    """rows[0] = Kopf. hl = {zeilenindex: farbe}; strike = Zeilen durchgestrichen."""
    def __init__(self, x, y, cols, rows, color='blue', title=None, rh=46, size=23, hl=None, strike=()):
        self.__dict__.update(locals()); del self.__dict__['self']
    def draw(self, d, img, hl=None):
        c, cf = COLORS[hl or self.color]
        x, y = self.x, self.y
        if self.title:
            draw_text(d, x + sum(self.cols) / 2, y - 24, self.title, font('xbold', 25), c)
        for ri, row in enumerate(self.rows):
            ry = y + ri * (self.rh + 8)
            rc, rf = c, cf
            if self.hl and ri in self.hl:
                rc, rf = COLORS[self.hl[ri]]
            rrect(d, x, ry, sum(self.cols), self.rh, 7, rc, rf if ri else rf)
            cx = x
            for ci, cell in enumerate(row):
                if ci:
                    d.line((s(cx), s(ry), s(cx), s(ry + self.rh)), fill=rc, width=s(1.5))
                draw_text(d, cx + self.cols[ci] / 2, ry + self.rh / 2, str(cell), font('xbold' if ri == 0 else 'reg', self.size), INK)
                cx += self.cols[ci]
            if ri in self.strike:
                d.line((s(x - 6), s(ry + self.rh / 2), s(x + sum(self.cols) + 6), s(ry + self.rh / 2)), fill=RED, width=s(3))

class Arrow(El):
    def __init__(self, pts, color=INK, head='filled', dashed=False, label=None, lpos=0.5, loff=(0, -16),
                 width=2, tail=None, size=19):
        self.__dict__.update(locals()); del self.__dict__['self']
    def draw(self, d, img, hl=None):
        col = COLORS[hl][0] if hl else self.color
        pts = [(s(a), s(b)) for a, b in self.pts]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if self.dashed:
                L = math.hypot(x2 - x1, y2 - y1); n = max(1, int(L / s(10)))
                for i in range(0, n, 2):
                    a, b = i / n, min(1, (i + 1) / n)
                    d.line((x1 + (x2 - x1) * a, y1 + (y2 - y1) * a, x1 + (x2 - x1) * b, y1 + (y2 - y1) * b), fill=col, width=s(self.width))
            else:
                d.line((x1, y1, x2, y2), fill=col, width=s(self.width))
        def tip(p_from, p_to, kind):
            (x1, y1), (x2, y2) = p_from, p_to
            ang = math.atan2(y2 - y1, x2 - x1); L = s(14)
            a = (x2 - L * math.cos(ang - 0.42), y2 - L * math.sin(ang - 0.42))
            b = (x2 - L * math.cos(ang + 0.42), y2 - L * math.sin(ang + 0.42))
            if kind == 'filled': d.polygon([(x2, y2), a, b], fill=col)
            elif kind == 'open': d.line([a, (x2, y2), b], fill=col, width=s(self.width))
            elif kind == 'triangle': d.polygon([(x2, y2), a, b], fill=BG, outline=col, width=s(2))
            elif kind in ('diamond', 'diamondf'):
                m = (x2 - L * 1.1 * math.cos(ang), y2 - L * 1.1 * math.sin(ang))
                e = (x2 - L * 2.2 * math.cos(ang), y2 - L * 2.2 * math.sin(ang))
                p = (m[0] + L * .5 * math.sin(ang), m[1] - L * .5 * math.cos(ang))
                q = (m[0] - L * .5 * math.sin(ang), m[1] + L * .5 * math.cos(ang))
                d.polygon([(x2, y2), p, e, q], fill=col if kind == 'diamondf' else BG, outline=col, width=s(2))
        if self.head: tip(pts[-2], pts[-1], self.head)
        if self.tail: tip(pts[1], pts[0], self.tail)
        if self.label:
            (x1, y1), (x2, y2) = self.pts[0], self.pts[-1] if len(self.pts) == 2 else self.pts[1]
            lx = x1 + (x2 - x1) * self.lpos + self.loff[0]; ly = y1 + (y2 - y1) * self.lpos + self.loff[1]
            draw_text(d, lx, ly, self.label, font('reg', self.size), INK)

class Circle(El):
    def __init__(self, x, y, r, kind='start', color=INK):
        self.__dict__.update(locals()); del self.__dict__['self']
    def draw(self, d, img, hl=None):
        x, y, r = s(self.x), s(self.y), s(self.r)
        if self.kind == 'start': d.ellipse((x - r, y - r, x + r, y + r), fill=self.color)
        elif self.kind == 'end':
            d.ellipse((x - r, y - r, x + r, y + r), outline=self.color, width=s(2.5))
            r2 = r * .6; d.ellipse((x - r2, y - r2, x + r2, y + r2), fill=self.color)
        elif self.kind == 'flowend':
            d.ellipse((x - r, y - r, x + r, y + r), outline=self.color, width=s(2.5), fill=BG)
            k = r * .7
            d.line((x - k, y - k, x + k, y + k), fill=self.color, width=s(2.5)); d.line((x - k, y + k, x + k, y - k), fill=self.color, width=s(2.5))
        elif self.kind == 'key':
            col = self.color
            d.ellipse((x - r, y - r, x + r, y + r), outline=col, width=s(4))
            d.line((x + r, y, x + r * 3.2, y), fill=col, width=s(5))
            d.line((x + r * 2.4, y, x + r * 2.4, y + r * .9), fill=col, width=s(5))
            d.line((x + r * 3.0, y, x + r * 3.0, y + r * .7), fill=col, width=s(5))

class Diamond(El):
    def __init__(self, x, y, w=46, h=46, color='blue', text=None):
        self.__dict__.update(locals()); del self.__dict__['self']
    def draw(self, d, img, hl=None):
        c, cf = COLORS[hl or self.color]
        x, y, w, h = self.x, self.y, self.w / 2, self.h / 2
        d.polygon([(s(x), s(y - h)), (s(x + w), s(y)), (s(x), s(y + h)), (s(x - w), s(y))], fill=cf, outline=c, width=s(2))
        if self.text: draw_text(d, x, y, self.text, font('bold', 18), INK)

class Bar(El):
    def __init__(self, x, y, w, h=9): self.a = (x, y, w, h)
    def draw(self, d, img, hl=None):
        x, y, w, h = self.a
        d.rectangle((s(x), s(y), s(x + w), s(y + h)), fill=INK)

class Code(El):
    def __init__(self, x, y, w, lines, size=24, color='gray', hl_lines=None, kw=()):
        self.__dict__.update(locals()); del self.__dict__['self']
    def draw(self, d, img, hl=None):
        c, cf = COLORS[self.color]
        lh = self.size * 1.55
        h = len(self.lines) * lh + 28
        rrect(d, self.x, self.y, self.w, h, 10, c, (250, 248, 242))
        for i, l in enumerate(self.lines):
            yy = self.y + 14 + lh * (i + .5)
            if self.hl_lines and i in self.hl_lines:
                hc = COLORS[self.hl_lines[i]][1]
                d.rectangle((s(self.x + 4), s(yy - lh / 2 + 2), s(self.x + self.w - 4), s(yy + lh / 2 - 2)), fill=hc)
            # Schlüsselwörter fett/blau
            xx = self.x + 18
            for tok in re.split(r'(\s+)', l):
                isk = tok.strip() in self.kw
                f = font('monob' if isk else 'mono', self.size)
                draw_text(d, xx, yy, tok, f, BLUE if isk else INK, 'lm')
                xx += text_w(tok, f) if tok.strip() else text_w(' ' * len(tok), f)

class Group(El):
    def __init__(self, *els): self.els = els
    def draw(self, d, img, hl=None):
        for e in self.els: e.draw(d, img, hl)

class Cross(El):
    def __init__(self, x, y, r=16, color=RED): self.a = (x, y, r, color)
    def draw(self, d, img, hl=None):
        x, y, r, c = self.a
        d.line((s(x - r), s(y - r), s(x + r), s(y + r)), fill=c, width=s(4)); d.line((s(x - r), s(y + r), s(x + r), s(y - r)), fill=c, width=s(4))

class Check(El):
    def __init__(self, x, y, r=16, color=GREEN): self.a = (x, y, r, color)
    def draw(self, d, img, hl=None):
        x, y, r, c = self.a
        d.line([(s(x - r), s(y)), (s(x - r * .3), s(y + r * .7)), (s(x + r), s(y - r * .8))], fill=c, width=s(4), joint='curve')

class Ring(El):
    """Roter Kringel (Hervorhebung)."""
    def __init__(self, x, y, w, h): self.a = (x, y, w, h)
    def draw(self, d, img, hl=None):
        x, y, w, h = self.a
        for k, off in enumerate((0, 3)):
            d.ellipse((s(x - w / 2 - off), s(y - h / 2 + off), s(x + w / 2 + off), s(y + h / 2 - off)), outline=RED, width=s(3))

# ---------- Untertitel ----------
def caption_chunks(text, maxc=22):
    words, out, cur = text.split(), [], ''
    for w in words:
        if cur and len(cur) + 1 + len(w) > maxc:
            out.append(cur); cur = w
        else:
            cur = (cur + ' ' + w).strip()
        if cur.endswith(('.', ',', ':', '?', '!')) and len(cur) > 8:
            out.append(cur); cur = ''
    if cur: out.append(cur)
    return out

def draw_caption(img, t):
    if not t: return
    d = ImageDraw.Draw(img)
    f = font('hand', 44)
    tw = text_w(t, f)
    x, y, ph, pv = 46, 1108, 16, 10
    d.rectangle((s(x), s(y), s(x + tw + 2 * ph), s(y + 44 + 2 * pv + 4)), fill=(221, 218, 209))
    draw_text(d, x + ph, y + pv + 26, t, f, (40, 42, 44), 'lm')

# ---------- Audio ----------
def tts(text, path):
    subprocess.run(['pico2wave', '-l', 'de-DE', '-w', path, text], check=True)
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()

# ---------- Rendern ----------
def render(segments, out, title_card=None, workdir='/tmp/shortwork'):
    shutil.rmtree(workdir, ignore_errors=True); os.makedirs(workdir)
    bg = paper()
    state = {}       # id -> [El, hl]
    order = []
    frames = []      # (pfad, dauer)
    audio = []
    n = [0]
    cache = {}

    def snap(alpha_ids=(), alpha=1.0, cap=''):
        img = bg.copy()
        d = ImageDraw.Draw(img)
        for i in order:
            el, hl = state[i]
            if i in alpha_ids and alpha < 1:
                layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
                el.draw(ImageDraw.Draw(layer), layer, hl)
                a = layer.split()[3].point(lambda p: int(p * alpha))
                layer.putalpha(a)
                img.paste(layer, (0, 0), layer)
            else:
                el.draw(d, img, hl)
        draw_caption(img, cap)
        small = img.resize((W, H), Image.LANCZOS)
        p = f'{workdir}/f{n[0]:05d}.png'; n[0] += 1
        small.save(p)
        return p

    pause = 0.32
    for si, seg in enumerate(segments):
        wav = f'{workdir}/a{si:03d}.wav'
        dur = tts(seg['say'], wav) + pause
        audio.append((wav, dur))
        new = []
        for op in seg.get('do', []):
            if op[0] == 'add':
                state[op[1]] = [op[2], None]
                if op[1] in order: order.remove(op[1])
                order.append(op[1]); new.append(op[1])
            elif op[0] == 'rm':
                for k in op[1:]:
                    state.pop(k, None)
                    if k in order: order.remove(k)
            elif op[0] == 'clear':
                state.clear(); order.clear()
            elif op[0] == 'hl':
                state[op[1]][1] = op[2]
        chunks = caption_chunks(seg.get('cap', seg['say']))
        total = sum(len(c) for c in chunks)
        t_used = 0
        fade_steps = 4 if new else 0
        for ci, c in enumerate(chunks):
            cd = dur * len(c) / total
            if ci == 0 and fade_steps:
                for k in range(1, fade_steps):
                    frames.append((snap(new, k / fade_steps, c), 1 / FPS))
                cd -= (fade_steps - 1) / FPS
            frames.append((snap(cap=c), max(cd, 1 / FPS)))
    # Audio zusammenfügen
    lst = f'{workdir}/audio.txt'
    with open(lst, 'w') as fh:
        for wav, dur in audio:
            fh.write(f"file '{wav}'\n")
            fh.write(f"file '{workdir}/sil.wav'\n")
    sr = 16000
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'anullsrc=r={sr}:cl=mono', '-t', str(pause), f'{workdir}/sil.wav'], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c:a', 'pcm_s16le', f'{workdir}/voice.wav'], check=True)
    vl = f'{workdir}/video.txt'
    with open(vl, 'w') as fh:
        for p, dur in frames:
            fh.write(f"file '{p}'\nduration {dur:.4f}\n")
        fh.write(f"file '{frames[-1][0]}'\n")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', vl, '-i', f'{workdir}/voice.wav',
                    '-af', 'highpass=f=80,lowpass=f=7000,acompressor=threshold=-18dB:ratio=3,loudnorm=I=-16:TP=-1.5,aresample=44100',
                    '-vf', f'fps={FPS},format=yuv420p', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-r', str(FPS),
                    '-c:a', 'aac', '-b:a', '96k', '-ac', '2', '-shortest', '-movflags', '+faststart', out], check=True)
    return sum(d for _, d in audio)

def title(t, sub, color=BLUE, tsize=50):
    return [('clear',),
            ('add', 'tag', Text(360, 470, 'AP2 · Anwendungsentwicklung', 22, MUTED, 'bold')),
            ('add', 't', Text(360, 560, t, tsize, INK, 'xbold')),
            ('add', 'u', Bar(210, 620 + (tsize * 1.3 if '\n' in t else 0), 300, 6)),
            ('add', 's', Text(360, 690 + (tsize * 1.3 if '\n' in t else 0), sub, 28, color, 'bold'))]
