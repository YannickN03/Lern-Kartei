// Markieren (Wörter antippen/überstreichen) und Stift/Radierer auf einer Kartenseite.
// ink = { marks: [[wortIndex, farbe1..3]], strokes: [{color, width, pts:[x,y,…] normiert auf Breite}] }
const Ink = (() => {
  function attach(face, ink, ctx) {
    // ctx: { tool(): 'none'|'mark'|'pen'|'erase', color(): {mark, pen}, changed(ink) }
    ink.marks = ink.marks || [];
    ink.strokes = ink.strokes || [];
    const scroll = face.querySelector('.scroll');
    const content = face.querySelector('.content');
    const canvas = document.createElement('canvas');
    canvas.className = 'inkcanvas';
    scroll.appendChild(canvas);
    const g = canvas.getContext('2d');
    let W = 1;

    function size() {
      const dpr = window.devicePixelRatio || 1;
      W = content.offsetWidth || 1;
      const H = Math.max(content.offsetHeight, scroll.clientHeight);
      canvas.style.width = W + 'px';
      canvas.style.height = H + 'px';
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      draw();
    }
    function line(s) {
      const p = s.pts;
      if (p.length < 2) return;
      g.strokeStyle = s.color; g.lineWidth = s.width * W; g.lineCap = g.lineJoin = 'round';
      g.globalAlpha = s.color === '#ffe45c' ? 0.55 : 1;
      g.beginPath(); g.moveTo(p[0] * W, p[1] * W);
      for (let i = 2; i < p.length; i += 2) g.lineTo(p[i] * W, p[i + 1] * W);
      if (p.length === 2) g.lineTo(p[0] * W + 0.1, p[1] * W);
      g.stroke(); g.globalAlpha = 1;
    }
    function draw() { g.clearRect(0, 0, canvas.width, canvas.height); ink.strokes.forEach(line); }
    const pos = e => { const r = canvas.getBoundingClientRect(); return [(e.clientX - r.left) / W, (e.clientY - r.top) / W]; };

    // Stift / Radierer
    let cur = null;
    canvas.addEventListener('pointerdown', e => {
      const t = ctx.tool();
      if (t !== 'pen' && t !== 'erase') return;
      e.preventDefault(); e.stopPropagation();
      canvas.setPointerCapture(e.pointerId);
      if (t === 'pen') { cur = { color: ctx.color().pen, width: 0.008, pts: pos(e) }; ink.strokes.push(cur); }
      else { cur = 'erase'; erase(pos(e)); }
      draw();
    });
    canvas.addEventListener('pointermove', e => {
      if (!cur) return;
      e.preventDefault();
      if (cur === 'erase') erase(pos(e)); else cur.pts.push(...pos(e).map(v => Math.round(v * 1e4) / 1e4));
      draw();
    });
    const end = () => { if (cur) { cur = null; ctx.changed(ink); } };
    canvas.addEventListener('pointerup', end);
    canvas.addEventListener('pointercancel', end);
    function erase([x, y]) {
      const r = 0.03;
      ink.strokes = ink.strokes.filter(s => {
        for (let i = 0; i < s.pts.length; i += 2) if (Math.hypot(s.pts[i] - x, s.pts[i + 1] - y) < r) return false;
        return true;
      });
    }

    // Markieren
    let painting = null; // 'add' | 'remove'
    const wordAt = e => { const el = document.elementFromPoint(e.clientX, e.clientY); return el && el.classList && el.classList.contains('w') && content.contains(el) ? el : null; };
    function apply(w) {
      const i = +w.dataset.i, c = ctx.color().mark;
      ink.marks = ink.marks.filter(m => m[0] !== i);
      w.classList.remove('m1', 'm2', 'm3');
      if (painting === 'add') { ink.marks.push([i, c]); w.classList.add('m' + c); }
    }
    content.addEventListener('pointerdown', e => {
      if (ctx.tool() !== 'mark') return;
      const w = wordAt(e);
      if (!w) return;
      e.stopPropagation();
      painting = /m[123]/.test(w.className) ? 'remove' : 'add';
      apply(w);
    });
    content.addEventListener('pointermove', e => {
      if (!painting) return;
      e.preventDefault();
      const w = wordAt(e);
      if (w) apply(w);
    });
    const stop = () => { if (painting) { painting = null; ctx.changed(ink); } };
    content.addEventListener('pointerup', stop);
    content.addEventListener('pointercancel', stop);
    content.addEventListener('pointerleave', stop);

    new ResizeObserver(size).observe(content);
    content.querySelectorAll('img').forEach(i => i.addEventListener('load', size));
    size();
    return { clear() { ink.marks = []; ink.strokes = []; content.querySelectorAll('.w').forEach(w => w.classList.remove('m1', 'm2', 'm3')); draw(); ctx.changed(ink); }, undo() { ink.strokes.pop(); draw(); ctx.changed(ink); } };
  }
  return { attach };
})();
