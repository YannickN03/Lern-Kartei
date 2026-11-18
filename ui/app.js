// LernKartei UI – Hash-Router, Screens, Lernmodus. Logik/Speicherung liegt in Rust (siehe api.js).
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const view = $('#view');
const esc = MD.esc;
const call = API.call;
const RATING = { new: 'Neu', nicht: 'Nicht', geht: 'Geht so', kann: 'Kann ich' };
const COLORS = ['#8b6cff', '#3ccf8e', '#ffb547', '#ff5d73', '#4cc3ff', '#ff8a3d', '#c36bff', '#7ad3c4'];
const MARK = { 1: '#ffe45c', 2: '#8ff0b8', 3: '#ffb3d1' };
const PEN = ['#e5364b', '#2f6bff', '#16a36a', '#1c1830'];

// ---------- Hilfen ----------
function toast(msg, ms = 2600) {
  const t = $('#toast');
  t.textContent = msg; t.hidden = false;
  clearTimeout(toast.t); toast.t = setTimeout(() => (t.hidden = true), ms);
}
async function safe(p, ok) {
  try { const r = await p; if (ok) toast(ok); return r; } catch (e) { toast('⚠️ ' + (e.message || e)); throw e; }
}
function sheet(html, bind) {
  const s = $('#sheet');
  s.innerHTML = `<div>${html}</div>`; s.hidden = false;
  s.onclick = e => { if (e.target === s) closeSheet(); };
  bind && bind(s.firstElementChild);
}
function closeSheet() { $('#sheet').hidden = true; $('#sheet').innerHTML = ''; }
function confirmSheet(text, yes, cb) {
  sheet(`<p>${esc(text)}</p><div class="row"><button class="ghost grow" data-x>Abbrechen</button><button class="danger grow" data-y>${esc(yes)}</button></div>`, el => {
    $('[data-x]', el).onclick = closeSheet;
    $('[data-y]', el).onclick = () => { closeSheet(); cb(); };
  });
}
const go = h => { location.hash = h; };
const bar = c => {
  const t = c.total || 1;
  return `<div class="bar"><i class="k" style="width:${c.kann / t * 100}%"></i><i class="g" style="width:${c.geht / t * 100}%"></i><i class="n" style="width:${c.nicht / t * 100}%"></i></div>`;
};
const legend = c => `<div class="legend"><span><i class="dot kann"></i>${c.kann} Kann ich</span><span><i class="dot geht"></i>${c.geht} Geht so</span><span><i class="dot nicht"></i>${c.nicht} Nicht</span><span><i class="dot"></i>${c.new} Neu</span></div>`;
const plain = s => String(s || '').replace(/```[\s\S]*?```/g, '[Code]').replace(/[*=`|#]/g, '').replace(/\s+/g, ' ').trim();

// Dateien wählen/speichern: Tauri-Dialog + fs (Android: content://-URIs), sonst <input type=file>.
async function pickFile(exts, binary = false) {
  const T = API.tauri;
  if (T && T.dialog && T.fs) {
    const path = await T.dialog.open({ multiple: false, filters: [{ name: 'Dateien', extensions: exts }] });
    if (!path) return null;
    const p = typeof path === 'string' ? path : path.path;
    const name = decodeURIComponent(p).split(/[\/\\:]/).pop();
    return { name, data: binary ? await T.fs.readFile(p) : await T.fs.readTextFile(p) };
  }
  return new Promise(res => {
    const i = document.createElement('input');
    i.type = 'file'; i.accept = exts.map(e => '.' + e).join(',');
    i.onchange = async () => {
      const f = i.files[0];
      if (!f) return res(null);
      res({ name: f.name, data: binary ? new Uint8Array(await f.arrayBuffer()) : await f.text() });
    };
    i.click();
  });
}
async function saveFile(name, text) {
  const T = API.tauri;
  if (T && T.dialog && T.fs) {
    const p = await T.dialog.save({ defaultPath: name, filters: [{ name: 'JSON', extensions: ['json'] }] });
    if (!p) return false;
    await T.fs.writeTextFile(p, text);
    return true;
  }
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], { type: 'application/json' }));
  a.download = name; a.click();
  return true;
}
async function copy(text) {
  try { await navigator.clipboard.writeText(text); }
  catch { const t = document.createElement('textarea'); t.value = text; document.body.appendChild(t); t.select(); document.execCommand('copy'); t.remove(); }
}
async function imageToDataUrl(bytes) {
  const url = URL.createObjectURL(new Blob([bytes]));
  const img = await new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = url; });
  const s = Math.min(1, 900 / Math.max(img.width, img.height));
  const c = document.createElement('canvas');
  c.width = Math.round(img.width * s); c.height = Math.round(img.height * s);
  c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
  URL.revokeObjectURL(url);
  return c.toDataURL('image/jpeg', 0.82);
}

// ---------- Router ----------
const routes = {
  '': home, deck: deckView, study: studyView, edit: editView, deckedit: deckEditView,
  import: importView, search: searchView, more: moreView, info: infoView, shorts: shortsView,
};
// Aufräumen beim Verlassen eines Screens (z. B. Videos stoppen)
let leaveFns = [];
const onLeave = fn => leaveFns.push(fn);
async function route() {
  closeSheet();
  leaveFns.splice(0).forEach(fn => { try { fn(); } catch (e) { console.warn(e); } });
  const [path, query] = location.hash.replace(/^#\/?/, '').split('?');
  const [name, ...args] = path.split('/').map(decodeURIComponent);
  const params = Object.fromEntries(new URLSearchParams(query || ''));
  document.body.classList.toggle('studying', name === 'study');
  $$('#tabs a').forEach(a => a.classList.toggle('on', a.dataset.tab === (name || 'home')));
  window.scrollTo(0, 0);
  try { await (routes[name] || home)(args, params); }
  catch (e) { view.innerHTML = `<p class="empty">⚠️ ${esc(e.message || e)}</p>`; }
}
window.addEventListener('hashchange', route);

// ---------- Startseite ----------
async function home() {
  const ov = await call('overview');
  const t = ov.totals;
  const pct = t.total ? Math.round(t.kann / t.total * 100) : 0;
  const cats = {};
  ov.decks.forEach(d => (cats[d.category || 'Ohne Kategorie'] ||= []).push(d));
  view.innerHTML = `
    <div class="top"><h1>LernKartei</h1><span class="pill">🔥 ${ov.streak} Tag${ov.streak === 1 ? '' : 'e'}</span></div>
    <div class="hero">
      <div class="ring" style="--p:${pct}"><b>${pct}%</b></div>
      <div class="grow"><div class="stats">
        <span>Karten</span><b>${t.total}</b><span>Fällig</span><b>${t.due}</b>
        <span>Heute</span><b>${ov.reviews_today}</b><span>Markiert ⭐</span><b>${t.flagged}</b>
      </div></div>
    </div>
    ${legend(t)}
    <div class="quick">
      <button class="primary" data-q="due"><b>${t.due}</b>Fällige lernen</button>
      <button data-q="weak"><b>${t.nicht + t.geht}</b>Schwächen</button>
      <button data-q="mix"><b>🎲</b>Zufallsmix 20</button>
    </div>
    ${Object.entries(cats).map(([cat, ds]) => `
      <section class="cat">
        <div class="cathead"><h2>${esc(cat)}</h2><button data-cat="${esc(cat)}">▶ Lernen</button></div>
        <div class="decks">${ds.map(d => `
          <div class="deck" style="--c:${esc(d.color || '#8b6cff')}" data-deck="${esc(d.id)}">
            <div class="t"><span>${esc(d.icon || '🗂️')}</span><span>${esc(d.name)}</span><span class="pill ${d.counts.due ? 'due' : ''}">${d.counts.due} fällig</span></div>
            ${bar(d.counts)}
            <div class="muted">${d.counts.total} Karten · ${d.counts.kann} kann ich · ${d.counts.nicht + d.counts.geht} offen</div>
          </div>`).join('')}</div>
      </section>`).join('')}
    ${ov.decks.length ? '' : '<p class="empty">Noch keine Decks. Importiere Karten oder lege ein Deck an.</p>'}
    <p style="margin-top:24px"><button class="ghost full" onclick="go('#/deckedit')">➕ Neues Deck / neue Kategorie</button></p>`;
  $$('[data-deck]').forEach(el => (el.onclick = () => go('#/deck/' + encodeURIComponent(el.dataset.deck))));
  $$('[data-cat]').forEach(b => (b.onclick = () => studySheet(ov.decks.filter(d => (d.category || 'Ohne Kategorie') === b.dataset.cat).map(d => d.id), b.dataset.cat)));
  $('[data-q=due]').onclick = () => startStudy([], 'due', false, 0);
  $('[data-q=weak]').onclick = () => startStudy([], 'weak', true, 0);
  $('[data-q=mix]').onclick = () => startStudy([], 'all', true, 20);
  shortsTeaser($('.quick'), null);
}

// Hinweis auf Shorts (Start: alle, Deck: nur passende); erscheint nur, wenn es Videos gibt.
async function shortsTeaser(after, deck) {
  try {
    const f = await call('shorts_feed', { filter: 'all', deck, shuffle: false });
    if (!f.total || !after.isConnected) return;
    const n = f.total - f.seen;
    const b = document.createElement('button');
    b.className = 'shortsteaser full';
    b.innerHTML = `<span>🎬</span><span class="grow"><b>Lern-Shorts${deck ? ' zum Thema' : ''}</b><br><small>${f.total} Video${f.total === 1 ? '' : 's'} · ${n ? n + ' neu' : 'alle gesehen'}</small></span><span>▶</span>`;
    b.onclick = () => go('#/shorts' + (deck ? '?deck=' + encodeURIComponent(deck) : ''));
    after.after(b);
  } catch (e) { console.warn(e); }
}

function studySheet(deckIds, title) {
  let mode = 'due', shuffle = false, limit = 0;
  const modes = { due: 'Fällig', all: 'Alle', weak: 'Schwächen', new: 'Neue', nicht: 'Nicht', geht: 'Geht so', kann: 'Kann ich', flagged: 'Markiert ⭐' };
  sheet(`<h2>${esc(title)} lernen</h2>
    <label>Welche Karten?</label><div class="seg" id="m">${Object.entries(modes).map(([k, v]) => `<button data-m="${k}" class="${k === mode ? 'on' : ''}">${v}</button>`).join('')}</div>
    <label style="margin-top:12px">Anzahl</label><div class="seg" id="l">${[0, 10, 20, 50].map(n => `<button data-l="${n}" class="${n === 0 ? 'on' : ''}">${n || 'Alle'}</button>`).join('')}</div>
    <label class="row" style="margin:14px 0"><input type="checkbox" id="sh" style="width:auto"> Reihenfolge mischen</label>
    <button class="primary full" id="go">▶ Starten</button>`, el => {
    $$('[data-m]', el).forEach(b => (b.onclick = () => { mode = b.dataset.m; $$('[data-m]', el).forEach(x => x.classList.toggle('on', x === b)); }));
    $$('[data-l]', el).forEach(b => (b.onclick = () => { limit = +b.dataset.l; $$('[data-l]', el).forEach(x => x.classList.toggle('on', x === b)); }));
    $('#sh', el).onchange = e => (shuffle = e.target.checked);
    $('#go', el).onclick = () => startStudy(deckIds, mode, shuffle, limit);
  });
}

// ---------- Deck ----------
async function deckView([id], params) {
  const d = await call('deck', { id });
  const filter = params.f || 'all';
  const c = { total: d.cards.length, new: 0, nicht: 0, geht: 0, kann: 0 };
  d.cards.forEach(x => c[x.progress.rating]++);
  const shown = d.cards.filter(x => filter === 'all' || (filter === 'flagged' ? x.flagged : x.progress.rating === filter));
  const chips = { all: `Alle ${c.total}`, new: `Neu ${c.new}`, nicht: `Nicht ${c.nicht}`, geht: `Geht so ${c.geht}`, kann: `Kann ich ${c.kann}`, flagged: '⭐' };
  view.innerHTML = `
    <div class="top"><button class="iconbtn" onclick="history.back()">←</button><h1>${esc(d.icon || '🗂️')} ${esc(d.name)}</h1><button class="iconbtn" id="menu">⋯</button></div>
    <p class="muted">${esc(d.category)}${d.description ? ' · ' + esc(d.description) : ''}</p>
    ${bar(c)}${legend(c)}
    <div class="row" style="margin:14px 0"><button class="primary grow" id="learn">▶ Lernen</button><button class="grow" id="add">➕ Karte</button></div>
    <div class="chips">${Object.entries(chips).map(([k, v]) => `<button data-f="${k}" class="${k === filter ? 'on' : ''}">${v}</button>`).join('')}</div>
    <div class="list">${shown.map(x => `
      <div class="item" data-c="${esc(x.id)}"><i class="dot ${x.progress.rating}"></i>
        <div class="txt"><div>${esc(plain(x.front))}</div><div class="muted">${esc(plain(x.back)).slice(0, 120)}</div></div>
        ${x.flagged ? '⭐' : ''}${x.image ? '🖼️' : ''}</div>`).join('') || '<p class="empty">Keine Karten in diesem Stapel.</p>'}</div>`;
  $$('[data-f]').forEach(b => (b.onclick = () => go(`#/deck/${encodeURIComponent(id)}?f=${b.dataset.f}`)));
  $('#learn').onclick = () => studySheet([id], d.name);
  shortsTeaser($('#learn').parentElement, id);
  $('#add').onclick = () => go('#/edit/' + encodeURIComponent(id));
  $$('[data-c]').forEach(el => (el.onclick = () => cardSheet(d, d.cards.find(x => x.id === el.dataset.c))));
  $('#menu').onclick = () => sheet(`<h2>${esc(d.name)}</h2><div class="stack">
      <button data-a="edit">✏️ Deck bearbeiten</button>
      <button data-a="export">📤 Deck exportieren (JSON)</button>
      <button data-a="reset">↺ Fortschritt zurücksetzen</button>
      <button class="danger" data-a="del">🗑 Deck löschen</button></div>`, el => {
    $('[data-a=edit]', el).onclick = () => go('#/deckedit/' + encodeURIComponent(id));
    $('[data-a=export]', el).onclick = () => exportSheet([id], d.name);
    $('[data-a=reset]', el).onclick = () => confirmSheet('Fortschritt dieses Decks zurücksetzen?', 'Zurücksetzen', async () => { await safe(call('reset_progress', { deck: id }), 'Zurückgesetzt'); route(); });
    $('[data-a=del]', el).onclick = () => confirmSheet(`Deck „${d.name}“ mit ${d.cards.length} Karten löschen?` + (d.builtin ? ' (Standard-Decks lassen sich unter „Mehr“ wiederherstellen.)' : ''), 'Löschen', async () => { await safe(call('delete_deck', { id }), 'Gelöscht'); go('#/'); });
  });
}

function faceHtml(text, side, card, deckName) {
  return `<div class="face ${side}"><header><span>${esc(deckName || '')}</span>${card.tags && card.tags.length ? `<span>· ${esc(card.tags.join(', '))}</span>` : ''}<span class="side">${side === 'front' ? 'Frage' : 'Antwort'}</span></header>
    <div class="scroll"><div class="content">${MD.render(text)}${side === 'front' && card.image ? `<img class="cardimg" src="${card.image}">` : ''}</div></div></div>`;
}

function cardSheet(d, card) {
  sheet(`<div class="preview"><div class="content">${MD.render(card.front)}</div></div>
    <div class="preview" style="margin-top:8px;background:#fffdf4"><div class="content">${MD.render(card.back)}</div></div>
    <p class="muted">Status: <b>${RATING[card.progress.rating]}</b> · Fach ${card.progress.box} · ${card.progress.reviews}× gelernt</p>
    <label>Einsortieren</label>
    <div class="rate"><button class="n" data-r="nicht">Nicht</button><button class="g" data-r="geht">Geht so</button><button class="k" data-r="kann">Kann ich</button></div>
    <div class="row" style="margin-top:10px"><button class="grow" data-a="edit">✏️ Bearbeiten</button><button class="grow" data-a="flag">${card.flagged ? '★ Entmarkieren' : '⭐ Markieren'}</button></div>
    <div class="row" style="margin-top:8px"><button class="grow" data-a="move">↪ Verschieben</button><button class="grow" data-a="new">↺ Als neu</button><button class="danger grow" data-a="del">🗑</button></div>`, el => {
    $$('.content', el).forEach(c => MD.wrapWords(c, []));
    const args = { deck: d.id, card: card.id };
    $$('[data-r]', el).forEach(b => (b.onclick = async () => { await safe(call('sort_card', { ...args, rating: b.dataset.r }), 'Einsortiert: ' + RATING[b.dataset.r]); route(); }));
    $('[data-a=new]', el).onclick = async () => { await safe(call('sort_card', { ...args, rating: 'new' })); route(); };
    $('[data-a=edit]', el).onclick = () => go(`#/edit/${encodeURIComponent(d.id)}/${encodeURIComponent(card.id)}`);
    $('[data-a=flag]', el).onclick = async () => { await safe(call('toggle_flag', args)); route(); };
    $('[data-a=del]', el).onclick = () => confirmSheet('Karte löschen?', 'Löschen', async () => { await safe(call('delete_card', args), 'Gelöscht'); route(); });
    $('[data-a=move]', el).onclick = async () => {
      const ov = await call('overview');
      sheet(`<h2>Verschieben nach…</h2><div class="stack">${ov.decks.filter(x => x.id !== d.id).map(x => `<button data-to="${esc(x.id)}">${esc(x.icon || '🗂️')} ${esc(x.name)}</button>`).join('')}</div>`, e2 => {
        $$('[data-to]', e2).forEach(b => (b.onclick = async () => { await safe(call('move_card', { from: d.id, card: card.id, to: b.dataset.to }), 'Verschoben'); route(); }));
      });
    };
  });
}

// ---------- Lernmodus ----------
let session = null;
const tool = { name: 'none', mark: 1, pen: PEN[0] };

async function startStudy(decks, mode, shuffle, limit) {
  const queue = await call('study', { decks, mode, limit, shuffle });
  if (!queue.length) { toast('Keine passenden Karten – alles erledigt 🎉'); closeSheet(); return; }
  session = { queue, idx: 0, stats: { nicht: 0, geht: 0, kann: 0 }, again: new Set(), decks, mode };
  go('#/study');
}

function studyView() {
  if (!session) return go('#/');
  if (session.idx >= session.queue.length) return studyDone();
  const s = session.queue[session.idx];
  const card = s.card;
  const total = session.queue.length;
  view.innerHTML = `
    <div class="studytop"><button class="iconbtn" id="quit">✕</button><div class="progress"><i style="width:${session.idx / total * 100}%"></i></div><span class="muted">${session.idx + 1}/${total}</span></div>
    <div class="stage"><div id="swipe"><div class="swipehint l">NICHT</div><div class="swipehint r">KANN ICH</div><div class="swipehint u">GEHT SO</div>
      <div class="card3d tool-${tool.name}" id="card">${faceHtml(card.front, 'front', card, s.deck_name)}${faceHtml(card.back, 'back', card, s.deck_name)}</div></div></div>
    <div class="tools" id="tools">
      <button data-t="none" title="Lesen">👆</button><button data-t="mark" title="Markieren">🖍️</button><button data-t="pen" title="Stift">✏️</button><button data-t="erase" title="Radierer">🧽</button>
      <span id="sw" class="row" style="flex-wrap:nowrap"></span>
      <button id="undo" title="Rückgängig">↶</button><button id="clr" title="Seite leeren">🗑</button>
      <button id="flag" title="Merken">${card.flagged ? '★' : '⭐'}</button><button id="ed" title="Bearbeiten">✎</button>
    </div>
    <div id="actions"></div>`;
  const el = $('#card');
  const save = side => ink => { clearTimeout(save[side]); save[side] = setTimeout(() => call('set_ink', { deck: s.deck_id, card: card.id, side, ink }).catch(e => toast('⚠️ ' + e)), 400); };
  const ctx = side => ({ tool: () => tool.name, color: () => ({ mark: tool.mark, pen: tool.pen }), changed: save(side) });
  const faces = { front: $('.face.front .content', el), back: $('.face.back .content', el) };
  MD.wrapWords(faces.front, (card.ink_front || {}).marks);
  MD.wrapWords(faces.back, (card.ink_back || {}).marks);
  const inks = {
    front: Ink.attach($('.face.front', el), card.ink_front || {}, ctx('front')),
    back: Ink.attach($('.face.back', el), card.ink_back || {}, ctx('back')),
  };
  const side = () => (el.classList.contains('flipped') ? 'back' : 'front');
  const flip = () => { el.classList.toggle('flipped'); actions(); };

  function tools() {
    $$('[data-t]').forEach(b => b.classList.toggle('on', b.dataset.t === tool.name));
    el.className = `card3d tool-${tool.name}${el.classList.contains('flipped') ? ' flipped' : ''}`;
    const sw = $('#sw');
    if (tool.name === 'mark') sw.innerHTML = Object.entries(MARK).map(([k, c]) => `<button class="swatch ${+k === tool.mark ? 'on' : ''}" style="background:${c}" data-mk="${k}"></button>`).join('');
    else if (tool.name === 'pen') sw.innerHTML = PEN.map(c => `<button class="swatch ${c === tool.pen ? 'on' : ''}" style="background:${c}" data-pc="${c}"></button>`).join('');
    else sw.innerHTML = '';
    $$('[data-mk]').forEach(b => (b.onclick = () => { tool.mark = +b.dataset.mk; tools(); }));
    $$('[data-pc]').forEach(b => (b.onclick = () => { tool.pen = b.dataset.pc; tools(); }));
  }
  function actions() {
    $('#actions').innerHTML = el.classList.contains('flipped')
      ? `<div class="rate"><button class="n" data-r="nicht">✗ Nicht<small>← wischen</small></button><button class="g" data-r="geht">~ Geht so<small>↑ wischen</small></button><button class="k" data-r="kann">✓ Kann ich<small>→ wischen</small></button></div><button class="ghost full" style="margin-top:8px" id="flipb">↻ Zurück zur Frage</button>`
      : `<button class="primary full" id="flipb" style="padding:15px">↻ Umdrehen</button><p class="muted" style="text-align:center">Tippe auf die Karte zum Umdrehen · wische zum Einsortieren</p>`;
    $('#flipb').onclick = flip;
    $$('[data-r]').forEach(b => (b.onclick = () => rate(b.dataset.r)));
  }
  async function rate(r) {
    try { await call('rate', { deck: s.deck_id, card: card.id, rating: r }); } catch (e) { return toast('⚠️ ' + e); }
    session.stats[r]++;
    if (r === 'nicht' && !session.again.has(card.id)) { session.again.add(card.id); session.queue.push(s); }
    session.idx++;
    studyView();
  }

  // Wischgesten (nur im Lese-Modus)
  const sw = $('#swipe');
  let start = null;
  sw.addEventListener('pointerdown', e => { if (tool.name !== 'none') return; start = { x: e.clientX, y: e.clientY, t: Date.now() }; });
  sw.addEventListener('pointermove', e => {
    if (!start) return;
    const dx = e.clientX - start.x, dy = e.clientY - start.y;
    if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
    sw.style.transform = `translate(${dx}px, ${Math.min(0, dy)}px) rotate(${dx / 25}deg)`;
    $('.swipehint.r', sw).style.opacity = Math.max(0, dx / 110);
    $('.swipehint.l', sw).style.opacity = Math.max(0, -dx / 110);
    $('.swipehint.u', sw).style.opacity = Math.abs(dx) < 60 ? Math.max(0, -dy / 110) : 0;
  });
  const end = e => {
    if (!start) return;
    const dx = e.clientX - start.x, dy = e.clientY - start.y, tap = Math.abs(dx) < 8 && Math.abs(dy) < 8 && Date.now() - start.t < 500;
    start = null;
    sw.style.transform = ''; $$('.swipehint', sw).forEach(h => (h.style.opacity = 0));
    if (tap) return flip();
    if (dx > 100) rate('kann'); else if (dx < -100) rate('nicht'); else if (dy < -100 && Math.abs(dx) < 60) rate('geht');
  };
  sw.addEventListener('pointerup', end);
  sw.addEventListener('pointercancel', () => { start = null; sw.style.transform = ''; });

  $$('[data-t]').forEach(b => (b.onclick = () => { tool.name = b.dataset.t; tools(); }));
  $('#undo').onclick = () => inks[side()].undo();
  $('#clr').onclick = () => inks[side()].clear();
  $('#flag').onclick = async () => { card.flagged = await call('toggle_flag', { deck: s.deck_id, card: card.id }); $('#flag').textContent = card.flagged ? '★' : '⭐'; toast(card.flagged ? 'Gemerkt ⭐' : 'Nicht mehr gemerkt'); };
  $('#ed').onclick = () => go(`#/edit/${encodeURIComponent(s.deck_id)}/${encodeURIComponent(card.id)}?back=study`);
  $('#quit').onclick = () => { session.idx = session.queue.length; studyDone(); };
  tools(); actions();
}

function studyDone() {
  const st = session.stats, n = st.nicht + st.geht + st.kann;
  view.innerHTML = `<div class="done"><div class="big">${n ? '🎉' : '👋'}</div><h1>${n ? 'Runde geschafft!' : 'Beendet'}</h1>
    <p class="muted">${n} Bewertungen</p>
    <div class="rate" style="margin:18px 0"><button class="k">✓ ${st.kann}<small>Kann ich</small></button><button class="g">~ ${st.geht}<small>Geht so</small></button><button class="n">✗ ${st.nicht}<small>Nicht</small></button></div>
    <div class="stack"><button class="primary" id="again">Schwächen wiederholen</button><button id="home">Zur Übersicht</button></div></div>`;
  $('#again').onclick = () => startStudy(session.decks, 'weak', true, 0);
  $('#home').onclick = () => { session = null; go('#/'); };
}

// ---------- Karte bearbeiten ----------
async function editView([deckId, cardId], params) {
  const ov = await call('overview');
  if (!ov.decks.length) { toast('Lege zuerst ein Deck an'); return go('#/deckedit'); }
  deckId = deckId || localStorage.getItem('lk-lastdeck') || ov.decks[0].id;
  const origDeck = deckId;
  let card = { front: '', back: '', tags: [], prio: 0, image: null };
  if (cardId) card = (await call('deck', { id: deckId })).cards.find(c => c.id === cardId) || card;
  const tb = id => `<div class="row" style="gap:4px">${[['**', '**', 'B'], ['==', '==', '🖍'], ['`', '`', '‹›'], ['\n```\n', '\n```\n', '{ }'], ['\n- ', '', '•'], ['\n| A | B |\n|---|---|\n| ', ' |  |\n', '▦']].map(([a, b, l]) => `<button class="iconbtn" data-w="${id}" data-a="${esc(a)}" data-b="${esc(b)}">${l}</button>`).join('')}</div>`;
  view.innerHTML = `
    <div class="top"><button class="iconbtn" onclick="history.back()">←</button><h1>${cardId ? 'Karte bearbeiten' : 'Neue Karte'}</h1></div>
    <div class="stack">
      <label>Deck<select id="deck">${ov.decks.map(d => `<option value="${esc(d.id)}" ${d.id === deckId ? 'selected' : ''}>${esc(d.category)} › ${esc(d.name)}</option>`).join('')}</select></label>
      <label>Vorderseite (Frage)</label>${tb('front')}<textarea id="front" placeholder="Was ist …?">${esc(card.front)}</textarea>
      <label>Rückseite (Antwort)</label>${tb('back')}<textarea id="back" style="min-height:170px" placeholder="Antwort … (**fett**, ==markiert==, \`code\`, - Liste)">${esc(card.back)}</textarea>
      <div class="row"><label class="grow">Tags (Komma)<input id="tags" value="${esc((card.tags || []).join(', '))}"></label>
        <label style="width:130px">Priorität<select id="prio">${['–', '1 niedrig', '2', '3 mittel', '4', '5 essentiell'].map((p, i) => `<option value="${i}" ${i === card.prio ? 'selected' : ''}>${p}</option>`).join('')}</select></label></div>
      <div class="row"><button id="img">🖼️ Bild ${card.image ? 'ändern' : 'einfügen'}</button>${card.image ? `<img class="thumb" src="${card.image}"><button class="danger" id="noimg">Bild entfernen</button>` : ''}</div>
      <div class="row"><button class="ghost grow" id="prev">👁 Vorschau</button><button class="primary grow" id="save">💾 Speichern</button></div>
      ${cardId ? '<button class="danger" id="del">🗑 Karte löschen</button>' : '<label class="row"><input type="checkbox" id="more" style="width:auto" checked> Danach weitere Karte anlegen</label>'}
    </div>`;
  $$('[data-w]').forEach(b => (b.onclick = () => {
    const t = $('#' + b.dataset.w), [s0, s1] = [t.selectionStart, t.selectionEnd];
    t.setRangeText(b.dataset.a + t.value.slice(s0, s1) + b.dataset.b, s0, s1, 'end'); t.focus();
  }));
  $('#img').onclick = async () => {
    const f = await pickFile(['png', 'jpg', 'jpeg', 'webp', 'gif'], true);
    if (!f) return;
    card.image = await safe(imageToDataUrl(f.data));
    collect(); editViewRefresh();
  };
  const noimg = $('#noimg');
  if (noimg) noimg.onclick = () => { card.image = null; collect(); editViewRefresh(); };
  function collect() {
    card.front = $('#front').value; card.back = $('#back').value;
    card.tags = $('#tags').value.split(',').map(s => s.trim()).filter(Boolean);
    card.prio = +$('#prio').value; deckId = $('#deck').value;
  }
  function editViewRefresh() { // Formular mit aktuellem Zwischenstand neu zeichnen
    const keep = { ...card };
    editView([deckId, cardId], params).then(() => { $('#front').value = keep.front; $('#back').value = keep.back; card = keep; });
  }
  $('#prev').onclick = () => {
    collect();
    sheet(`<div class="stage"><div class="card3d" id="pc" style="height:50vh">${faceHtml(card.front, 'front', card, '')}${faceHtml(card.back, 'back', card, '')}</div></div><button class="full" id="pf">↻ Umdrehen</button>`, el => {
      $('#pf', el).onclick = () => $('#pc', el).classList.toggle('flipped');
      $('#pc', el).onclick = () => $('#pc', el).classList.toggle('flipped');
    });
  };
  $('#save').onclick = async () => {
    collect();
    const input = { id: cardId || null, front: card.front, back: card.back, tags: card.tags, prio: card.prio, image: card.image || null };
    await safe(call('upsert_card', { deck: cardId ? origDeck : deckId, card: input }), 'Gespeichert ✓');
    localStorage.setItem('lk-lastdeck', deckId);
    if (cardId && origDeck !== deckId) await call('move_card', { from: origDeck, card: cardId, to: deckId });
    if (params.back === 'study' && session) {
      const cur = session.queue[session.idx];
      Object.assign(cur.card, { front: card.front, back: card.back, tags: card.tags, image: card.image, ink_front: {}, ink_back: {} });
      return go('#/study');
    }
    if (!cardId && $('#more') && $('#more').checked) { route(); return; }
    history.back();
  };
  const del = $('#del');
  if (del) del.onclick = () => confirmSheet('Karte löschen?', 'Löschen', async () => { await safe(call('delete_card', { deck: deckId, card: cardId }), 'Gelöscht'); history.back(); });
}

// ---------- Deck anlegen/bearbeiten ----------
async function deckEditView([id]) {
  const ov = await call('overview');
  const d = id ? await call('deck', { id }) : { name: '', category: '', description: '', color: COLORS[0], icon: '🗂️' };
  const cats = [...new Set(ov.decks.map(x => x.category))];
  view.innerHTML = `
    <div class="top"><button class="iconbtn" onclick="history.back()">←</button><h1>${id ? 'Deck bearbeiten' : 'Neues Deck'}</h1></div>
    <div class="stack">
      <label>Name<input id="n" value="${esc(d.name)}" placeholder="z. B. SQL-Joins"></label>
      <label>Lernkategorie<input id="c" list="cats" value="${esc(d.category)}" placeholder="z. B. Datenbanken"><datalist id="cats">${cats.map(c => `<option value="${esc(c)}">`).join('')}</datalist></label>
      <label>Beschreibung<input id="ds" value="${esc(d.description)}"></label>
      <div class="row"><label style="width:90px">Symbol<input id="i" value="${esc(d.icon || '🗂️')}" maxlength="4"></label>
        <div class="grow"><label>Farbe</label><div class="row" id="cols">${COLORS.map(c => `<button class="swatch ${c === d.color ? 'on' : ''}" style="background:${c}" data-col="${c}"></button>`).join('')}</div></div></div>
      <button class="primary" id="save">💾 Speichern</button>
    </div>`;
  let color = d.color || COLORS[0];
  $$('[data-col]').forEach(b => (b.onclick = () => { color = b.dataset.col; $$('[data-col]').forEach(x => x.classList.toggle('on', x === b)); }));
  $('#save').onclick = async () => {
    const deck = { id: id || null, name: $('#n').value, category: $('#c').value, description: $('#ds').value, color, icon: $('#i').value };
    const nid = await safe(call('upsert_deck', { deck }), 'Gespeichert ✓');
    location.replace('#/deck/' + encodeURIComponent(nid));
  };
}

// ---------- Import ----------
const TEMPLATE = `{
  "name": "Mein Deck",
  "category": "Eigene Karten",
  "description": "optional",
  "color": "#8b6cff",
  "icon": "📘",
  "cards": [
    { "front": "Was bedeutet ACID?", "back": "**A**tomarität, **C**onsistency, **I**solation, **D**auerhaftigkeit", "tags": ["SQL"], "prio": 4 },
    { "front": "Port von HTTPS?", "back": "==443== (TCP)" }
  ]
}`;
async function importView() {
  const ov = await call('overview');
  view.innerHTML = `
    <div class="top"><h1>Karten importieren</h1></div>
    <p class="muted">Formate: <b>JSON</b> (Deck, Deckliste oder Kartenliste), <b>CSV/TSV</b> (Vorderseite;Rückseite;Tags), <b>Text/Markdown</b> (<code>Frage :: Antwort</code>, <code>F:</code>/<code>A:</code>-Blöcke oder <code>## Frage</code> + Antwort).</p>
    <div class="stack">
      <button class="primary" id="file">📂 Datei auswählen</button>
      <label>…oder Inhalt einfügen<textarea id="txt" placeholder="F: Frage\nA: Antwort"></textarea></label>
      <div class="row"><label class="grow">Format<select id="fmt"><option value="">Automatisch</option><option value="x.json">JSON</option><option value="x.csv">CSV/TSV</option><option value="x.txt">Text/Markdown</option></select></label></div>
      <label>Ziel<select id="target"><option value="">Neues Deck</option>${ov.decks.map(d => `<option value="${esc(d.id)}">→ ${esc(d.name)}</option>`).join('')}</select></label>
      <div class="row" id="newdeck"><label class="grow">Deckname<input id="dn" placeholder="aus Datei"></label><label class="grow">Kategorie<input id="dc" placeholder="Eigene Karten"></label></div>
      <button id="go">📥 Text importieren</button>
    </div>
    <h2>JSON-Vorlage für neue Karten</h2>
    <p class="muted">Erstelle Karten z. B. mit einer KI oder im Editor als JSON und importiere sie hier. Unterstützt Markdown: <code>**fett**</code>, <code>==markiert==</code>, <code>\`code\`</code>, Code-Blöcke, Listen, Tabellen.</p>
    <pre style="background:var(--bg2);padding:12px;border-radius:12px;overflow:auto;font-size:.8rem">${esc(TEMPLATE)}</pre>
    <div class="row"><button class="grow" id="cp">📋 Vorlage kopieren</button><button class="grow" id="use">✍️ In Feld übernehmen</button></div>`;
  $('#target').onchange = e => ($('#newdeck').style.display = e.target.value ? 'none' : '');
  const run = async (name, content) => {
    const fmt = $('#fmt').value;
    const r = await safe(call('import_text', { fileName: fmt || name, content, deckName: $('#dn').value, category: $('#dc').value, target: $('#target').value || null }));
    toast(`✓ ${r.cards} Karten importiert (${r.decks.join(', ')})`, 4000);
    go('#/');
  };
  $('#file').onclick = async () => { const f = await pickFile(['json', 'csv', 'tsv', 'txt', 'md']).catch(e => toast('⚠️ ' + e)); if (f) run(f.name, f.data); };
  $('#go').onclick = () => { const t = $('#txt').value; if (!t.trim()) return toast('Kein Inhalt'); run('eingefuegt.txt', t); };
  $('#cp').onclick = async () => { await copy(TEMPLATE); toast('Vorlage kopiert'); };
  $('#use').onclick = () => { $('#txt').value = TEMPLATE; };
}

function exportSheet(decks, title) {
  sheet(`<h2>Export: ${esc(title)}</h2>
    <label class="row" style="margin-bottom:12px"><input type="checkbox" id="wp" style="width:auto" checked> Mit Lernfortschritt & Markierungen</label>
    <div class="stack"><button class="primary" id="sv">💾 Als Datei speichern</button><button id="cp">📋 In Zwischenablage kopieren</button></div>`, el => {
    const get = () => call('export_json', { decks, withProgress: $('#wp', el).checked });
    const fname = 'lernkartei-' + title.toLowerCase().replace(/[^a-z0-9]+/g, '-') + '.json';
    $('#sv', el).onclick = async () => { if (await safe(saveFile(fname, await get()))) { toast('Gespeichert ✓'); closeSheet(); } };
    $('#cp', el).onclick = async () => { await copy(await get()); toast('Kopiert ✓'); closeSheet(); };
  });
}

// ---------- Suche ----------
async function searchView(_, params) {
  view.innerHTML = `<div class="top"><h1>Suche</h1></div><input id="q" type="search" placeholder="Begriff, z. B. JOIN, Scrum, DSGVO…" value="${esc(params.q || '')}"><div class="list" id="res"></div>`;
  const q = $('#q');
  let t;
  const run = async () => {
    const res = await call('search', { query: q.value });
    $('#res').innerHTML = res.map((s, i) => `<div class="item" data-i="${i}"><i class="dot ${s.card.progress.rating}"></i><div class="txt"><div>${esc(plain(s.card.front))}</div><div class="muted">${esc(s.deck_name)}</div></div></div>`).join('') || (q.value ? '<p class="empty">Nichts gefunden.</p>' : '');
    $$('[data-i]').forEach(el => (el.onclick = () => { const s = res[+el.dataset.i]; cardSheet({ id: s.deck_id }, s.card); }));
  };
  q.oninput = () => { clearTimeout(t); t = setTimeout(() => { history.replaceState(null, '', '#/search?q=' + encodeURIComponent(q.value)); run(); }, 220); };
  if (q.value) run();
  q.focus();
}

// ---------- Mehr ----------
function moreView() {
  view.innerHTML = `<div class="top"><h1>Mehr</h1></div>
    <div class="stack">
      <button data-a="info">📋 Prüfungsinfo AP2 FIAE</button>
      <button data-a="deck">➕ Neues Deck / Kategorie</button>
      <button data-a="export">📤 Alles exportieren (Backup)</button>
      <button data-a="restore">♻️ Standard-Inhalte wiederherstellen</button>
      <button data-a="shorts">🎬 Shorts: „gesehen“ zurücksetzen</button>
      <button class="danger" data-a="reset">↺ Gesamten Lernfortschritt zurücksetzen</button>
    </div>
    <h2>So funktioniert's</h2>
    <p class="muted">Jede Karte landet nach dem Umdrehen in einem von drei Stapeln: <b style="color:var(--kann)">Kann ich</b>, <b style="color:var(--geht)">Geht so</b> oder <b style="color:var(--nicht)">Nicht</b>. Dahinter steckt ein Leitner-System: „Kann ich“ schiebt die Karte ein Fach weiter (Wiederholung nach 1, 3, 7, 14, 30 Tagen), „Geht so“ kommt morgen wieder, „Nicht“ noch in derselben Runde.</p>
    <p class="muted">🎬 <b>Shorts</b>: kurze Lernvideos zum Durchwischen. Tippen = Pause, Doppeltippen = merken ❤️, ⏩ ändert das Tempo, 📚 springt zu den passenden Karten.</p>
    <p class="muted">Im Lernmodus: 🖍️ Wörter antippen/überstreichen zum Markieren (3 Farben), ✏️ frei zeichnen, 🧽 radieren. Markierungen werden pro Karte gespeichert.</p>
    <p class="muted">Alle Daten liegen nur auf deinem Gerät. Regelmäßig exportieren = Backup.</p>
    <p class="muted">LernKartei 0.2 · Open Source · <a href="https://github.com/YannickN03/Lern-Kartei">GitHub</a>${API.mock ? ' · <b>Browser-Vorschau</b>' : ''}</p>`;
  $('[data-a=info]').onclick = () => go('#/info');
  $('[data-a=deck]').onclick = () => go('#/deckedit');
  $('[data-a=export]').onclick = () => exportSheet([], 'alles');
  $('[data-a=restore]').onclick = async () => { const r = await safe(call('restore_builtin')); toast(`✓ ${r.cards_added} Karten ergänzt, ${r.cards_updated} aktualisiert`); };
  $('[data-a=shorts]').onclick = async () => { await safe(call('shorts_reset'), 'Shorts wieder als neu markiert'); };
  $('[data-a=reset]').onclick = () => confirmSheet('Wirklich den gesamten Lernfortschritt löschen? Karten bleiben erhalten.', 'Alles zurücksetzen', async () => { await safe(call('reset_progress', { deck: null }), 'Zurückgesetzt'); });
}

function infoView() {
  view.innerHTML = `<div class="top"><button class="iconbtn" onclick="history.back()">←</button><h1>Prüfungsinfo AP2</h1></div>
  <div class="info">
    <p class="muted">Fachinformatiker/-in Anwendungsentwicklung, Ausbildungsordnung 2020 · Prüfungskatalog der AkA, Fassung Okt. 2024, gültig für Prüfungen ab 2025.</p>
    <table><tr><th>Prüfungsbereich</th><th>Form</th><th>Gew.</th></tr>
      <tr><td>AP1: Einrichten eines IT-gestützten Arbeitsplatzes</td><td>90 Min. schriftlich</td><td>20 %</td></tr>
      <tr><td>Planen und Umsetzen eines Softwareprojektes (betriebl. Projekt)</td><td>80 Std. + Doku, 15 Min. Präsentation + 15 Min. Fachgespräch</td><td>50 %</td></tr>
      <tr><td>Planen eines Softwareproduktes</td><td>90 Min., ungebundene Aufgaben</td><td>10 %</td></tr>
      <tr><td>Entwicklung und Umsetzung von Algorithmen</td><td>90 Min., ungebundene Aufgaben (SQL-Beiblatt)</td><td>10 %</td></tr>
      <tr><td>Wirtschafts- und Sozialkunde</td><td>60 Min., gebundene Aufgaben (Multiple Choice)</td><td>10 %</td></tr></table>
    <h2>Bestehensregeln</h2>
    <ul><li>Gesamtergebnis aus Teil 1 + Teil 2 mind. „ausreichend“ (50 Punkte)</li><li>Ergebnis von Teil 2 mind. „ausreichend“</li><li>Projektbereich (Planen und Umsetzen) mind. „ausreichend“</li><li>mind. zwei der drei übrigen AP2-Bereiche mind. „ausreichend“</li><li>kein AP2-Bereich „ungenügend“</li></ul><p class="muted">Mündliche Ergänzungsprüfung (ca. 15 Min.) in einem schriftlichen AP2-Bereich auf Antrag möglich.</p>
    <h2>Änderungen im Katalog ab 2025</h2>
    <ul><li><b>Gestrichen:</b> Struktogramm und Programmablaufplan (PAP)</li>
      <li><b>Neu/verstärkt:</b> BPMN 2.0, UML-Aktivitätsdiagramm, Sortieralgorithmen (Bubble-, Selection-, Insertion-Sort), KI-Grundlagen, Nachhaltigkeit/Green IT</li>
      <li><b>Von AP1 nach AP2 verschoben:</b> SQL und RAID</li></ul>
    <h2>AP1-Themen, die in AP2 wiederkommen</h2>
    <p>Laut Verordnung fließen AP1-Inhalte nur ein, soweit für die berufliche Handlungsfähigkeit nötig – in der Praxis tauchen aber regelmäßig auf: Schutzziele & IT-Sicherheit, DSGVO, Netzwerkgrundlagen (OSI, IP, Subnetting), Wirtschaftlichkeit (Angebotsvergleich, Nutzwertanalyse), Projektmanagement, Qualitätssicherung, Lizenzen & Verträge. Diese Karten tragen den Tag <code>AP1</code>.</p>
    <h2>Prioritäten in den Karten</h2>
    <p>5 = essentiell (in fast jeder Prüfung), 4 = sehr hoch, 3 = hoch, 2 = mittel, 1 = selten. Die Einordnung orientiert sich an der Häufigkeitsauswertung von ap2-fiae.de.</p>
    <h2>Quellen</h2>
    <ul><li><a href="https://www.ap2-fiae.de/">ap2-fiae.de – AP2 Lernhub (Themenstruktur, Priorisierung)</a></li>
      <li><a href="https://www.ihk.de/hannover/hauptnavigation/ausbildung-und-weiterbildung/ausbildung/ausbildung-a-z/neuordnungen/pruefungskataloge-it-berufe-6438900">IHK Hannover – Prüfungskataloge IT-Berufe</a></li>
      <li><a href="https://www.gesetze-im-internet.de/fiausbv/">Fachinformatiker-Ausbildungsverordnung (FIAusbV)</a></li></ul>
    <p class="muted">Ohne Gewähr – maßgeblich ist der offizielle Prüfungskatalog (u-form Verlag).</p>
  </div>`;
}

route();
