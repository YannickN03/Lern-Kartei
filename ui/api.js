// Brücke zum Rust-Backend. Ohne Tauri (Browser-Vorschau via `python3 -m http.server` im Repo-Root)
// springt ein einfacher Mock mit localStorage ein – nur für UI-Entwicklung gedacht.
const API = (() => {
  const T = window.__TAURI__;
  if (T && T.core) {
    const call = (cmd, args) => T.core.invoke(cmd, args || {});
    return { call, tauri: T, mock: false };
  }

  // ---------- Browser-Mock ----------
  const KEY = 'lk-mock';
  let lib = JSON.parse(localStorage.getItem(KEY) || 'null');
  const save = () => localStorage.setItem(KEY, JSON.stringify(lib));
  const now = () => Math.floor(Date.now() / 1000), today = () => Math.floor(now() / 86400);
  const IV = [0, 1, 3, 7, 14, 30];
  const prog = () => ({ rating: 'new', box: 0, due: 0, reviews: 0, lapses: 0, last: 0 });
  const uid = () => 'm' + Math.random().toString(36).slice(2, 12);
  async function init() {
    if (lib) return;
    lib = { decks: [], settings: { streak: 0, streak_day: 0, reviews_today: 0 } };
    try {
      const html = await (await fetch('../content/decks/')).text();
      const files = [...html.matchAll(/href="([^"]+\.json)"/g)].map(m => m[1]);
      for (const f of files) {
        const d = await (await fetch('../content/decks/' + f)).json();
        d.id = d.id || f.replace('.json', '');
        d.builtin = true;
        d.cards.forEach((c, i) => Object.assign(c, { id: d.id + i, progress: prog(), tags: c.tags || [], prio: c.prio || 0 }));
        lib.decks.push(d);
      }
    } catch (e) { console.warn(e); }
    save();
  }
  const ready = init();
  const D = id => lib.decks.find(d => d.id === id);
  const C = (d, c) => D(d).cards.find(x => x.id === c);
  const due = c => c.progress.rating === 'new' || c.progress.due <= today();
  const match = (c, m) => ({ due: due(c), all: true, weak: ['nicht', 'geht'].includes(c.progress.rating), new: c.progress.rating === 'new', flagged: c.flagged, nicht: c.progress.rating === 'nicht', geht: c.progress.rating === 'geht', kann: c.progress.rating === 'kann' })[m];
  function counts(d) {
    const o = { total: d.cards.length, new: 0, nicht: 0, geht: 0, kann: 0, due: 0, flagged: 0 };
    d.cards.forEach(c => { o[c.progress.rating]++; o.due += due(c); o.flagged += !!c.flagged; });
    return o;
  }
  function rate(p, r) {
    if (r === 'nicht') { p.box = 0; p.due = today(); }
    if (r === 'geht') { p.box = Math.max(1, p.box - 1); p.due = today() + 1; }
    if (r === 'kann') { p.box = Math.min(5, p.box + 1); p.due = today() + IV[p.box]; }
    p.rating = r; p.reviews++; p.last = now();
  }
  const sc = (d, c) => ({ deck_id: d.id, deck_name: d.name, color: d.color, card: c });
  const H = {
    overview() {
      const t = { total: 0, new: 0, nicht: 0, geht: 0, kann: 0, due: 0, flagged: 0 };
      const decks = lib.decks.map(d => { const c = counts(d); for (const k in t) t[k] += c[k]; return { ...d, cards: undefined, counts: c }; });
      return { decks, totals: t, streak: lib.settings.streak, reviews_today: lib.settings.reviews_today };
    },
    deck: a => D(a.id),
    study: a => {
      let out = lib.decks.filter(d => !a.decks.length || a.decks.includes(d.id)).flatMap(d => d.cards.filter(c => match(c, a.mode)).map(c => sc(d, c)));
      if (a.shuffle) out.sort(() => Math.random() - .5);
      return a.limit ? out.slice(0, a.limit) : out;
    },
    rate: a => { const c = C(a.deck, a.card); rate(c.progress, a.rating); lib.settings.reviews_today++; lib.settings.streak = Math.max(1, lib.settings.streak); return c; },
    sort_card: a => { const c = C(a.deck, a.card); rate(c.progress, a.rating); return c; },
    set_ink: a => { C(a.deck, a.card)[a.side === 'back' ? 'ink_back' : 'ink_front'] = a.ink; },
    toggle_flag: a => (C(a.deck, a.card).flagged = !C(a.deck, a.card).flagged),
    upsert_card: a => {
      const d = D(a.deck); let c = a.card.id && d.cards.find(x => x.id === a.card.id);
      if (!c) { c = { id: uid(), progress: prog() }; d.cards.push(c); }
      Object.assign(c, a.card, { id: c.id }); return c;
    },
    delete_card: a => { D(a.deck).cards = D(a.deck).cards.filter(c => c.id !== a.card); },
    move_card: a => { const c = C(a.from, a.card); H.delete_card({ deck: a.from, card: a.card }); D(a.to).cards.push(c); },
    upsert_deck: a => { let d = a.deck.id && D(a.deck.id); if (!d) { d = { id: uid(), cards: [] }; lib.decks.push(d); } Object.assign(d, a.deck, { id: d.id }); return d.id; },
    delete_deck: a => { lib.decks = lib.decks.filter(d => d.id !== a.id); },
    import_text: a => {
      const v = JSON.parse(a.content); const cards = (v.cards || v).map(c => ({ front: c.front || c.q, back: c.back || c.a, tags: c.tags || [], id: uid(), progress: prog() }));
      lib.decks.push({ id: uid(), name: v.name || a.deckName || 'Import', category: v.category || a.category || 'Eigene Karten', color: '#7c5cff', cards });
      return { cards: cards.length, decks: [v.name || 'Import'] };
    },
    export_json: a => JSON.stringify({ format: 'lernkartei', decks: lib.decks.filter(d => !a.decks.length || a.decks.includes(d.id)) }, null, 2),
    search: a => { const q = a.query.toLowerCase(); return lib.decks.flatMap(d => d.cards.filter(c => (c.front + c.back + c.tags.join()).toLowerCase().includes(q)).map(c => sc(d, c))).slice(0, 200); },
    reset_progress: a => lib.decks.filter(d => !a.deck || d.id === a.deck).forEach(d => d.cards.forEach(c => (c.progress = prog()))),
    restore_builtin: () => { localStorage.removeItem(KEY); location.reload(); },
  };
  async function call(cmd, args) {
    await ready;
    const r = H[cmd](args || {});
    save();
    return JSON.parse(JSON.stringify(r ?? null));
  }
  return { call, tauri: null, mock: true };
})();
