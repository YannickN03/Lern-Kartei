// Lern-Shorts: Hochkant-Videos zum Durchscrollen (Scroll-Snap, Autoplay des sichtbaren Videos).
// Logik (Katalog, Reihenfolge, Gesehen/Gemerkt) liegt in Rust: crates/core/src/shorts.rs.
const SHORTS = {
  speeds: [1, 1.25, 1.5, 2],
  pref(key, def) { try { const v = localStorage.getItem('lk-shorts-' + key); return v === null ? def : JSON.parse(v); } catch { return def; } },
  setPref(key, v) { try { localStorage.setItem('lk-shorts-' + key, JSON.stringify(v)); } catch { /* egal */ } },
};

async function shortsView(_, params) {
  const filter = params.f || 'all';
  const deck = params.deck || null;
  const shuffle = params.mix === '1';
  const feed = await call('shorts_feed', { filter, deck, shuffle });
  document.body.classList.add('shortsmode');
  const items = feed.items;
  const chips = { all: 'Für dich', new: 'Neu', liked: '❤️ Gemerkt' };
  const q = o => '#/shorts?' + new URLSearchParams(Object.entries({ f: filter, deck, mix: shuffle ? '1' : '', ...o }).filter(([, v]) => v)).toString();
  const upcoming = feed.upcoming.length ? `<div class="upcoming"><h2>🎬 Video folgt</h2>${feed.upcoming.map(s => `<div class="item"><div class="txt"><div>${esc(s.title)}</div><div class="muted">${esc(s.description || '')}</div></div></div>`).join('')}</div>` : '';
  const empty = !feed.total
    ? `<div class="short endcard"><div><div class="big">🎬</div><h1>Noch keine Shorts${deck ? ' zu diesem Thema' : ''}</h1><p class="muted">${feed.upcoming.length ? 'Die Videos sind angekündigt und kommen mit einem der nächsten App-Updates.' : 'Neue Lernvideos kommen mit einem der nächsten App-Updates.'}</p>${upcoming}</div></div>`
    : !items.length
      ? `<div class="short endcard"><div><div class="big">${filter === 'liked' ? '❤️' : '✅'}</div><h1>${filter === 'liked' ? 'Noch nichts gemerkt' : 'Alles gesehen!'}</h1><p class="muted">${filter === 'liked' ? 'Doppeltippen oder ❤️ merkt sich ein Short.' : `Du hast alle ${feed.total} Shorts angeschaut.`}</p><button class="primary" data-go="${esc(q({ f: 'all' }))}">Alle Shorts</button></div></div>`
      : '';
  view.innerHTML = `
    <div class="shortsbar">
      ${deck ? '<button class="iconbtn" onclick="history.back()">←</button>' : ''}
      <div class="chips">${Object.entries(chips).map(([k, v]) => `<button data-f="${k}" class="${k === filter ? 'on' : ''}">${v}</button>`).join('')}</div>
      <button class="iconbtn ${shuffle ? 'on' : ''}" id="mix" title="Mischen">🔀</button>
      <span class="pill">${feed.seen}/${feed.total}</span>
    </div>
    <div class="feed" id="feed">
      ${items.map((it, i) => `
        <section class="short" data-i="${i}">
          <video playsinline webkit-playsinline preload="${i < 2 ? 'auto' : 'metadata'}" data-src="shorts/${encodeURIComponent(it.file)}"></video>
          <div class="tapzone"></div>
          <div class="playhint">▶</div>
          <div class="heart">❤️</div>
          <div class="ov">
            ${it.deck_name ? `<button class="deckchip" data-deck="${esc(it.deck)}">${esc(it.deck_icon || '🗂️')} ${esc(it.deck_name)}</button>` : ''}
            <h3>${esc(it.title)}${it.seen ? ' <span class="pill">✓ gesehen</span>' : ''}</h3>
            ${it.description ? `<p>${esc(it.description)}</p>` : ''}
            ${it.tags && it.tags.length ? `<div class="tags">${it.tags.map(t => '#' + esc(t)).join(' ')}</div>` : ''}
          </div>
          <div class="side">
            <button data-like class="${it.liked ? 'on' : ''}" aria-label="Merken">${it.liked ? '❤️' : '🤍'}<small>Merken</small></button>
            ${it.deck_name ? `<button data-learn="${esc(it.deck)}" aria-label="Karten lernen">📚<small>Karten</small></button>` : ''}
            <button data-speed aria-label="Tempo">⏩<small>1×</small></button>
            <button data-mute aria-label="Ton">🔊<small>Ton</small></button>
          </div>
          <div class="seek"><i></i></div>
        </section>`).join('')}
      ${empty}
      ${items.length ? `<div class="short endcard"><div><div class="big">🎉</div><h1>Ende des Feeds</h1><p class="muted">${feed.seen}/${feed.total} gesehen</p>
        <div class="stack"><button class="primary" data-go="${esc(q({ mix: '1', f: 'all' }))}">🔀 Nochmal gemischt</button>${deck ? `<button data-learn="${esc(deck)}">📚 Karten zum Thema lernen</button>` : '<button data-go="#/">Zur Übersicht</button>'}</div>${upcoming}</div></div>` : ''}
    </div>`;

  $$('[data-f]').forEach(b => (b.onclick = () => go(q({ f: b.dataset.f }))));
  $('#mix').onclick = () => go(q({ mix: shuffle ? '' : '1' }));
  $$('[data-go]').forEach(b => (b.onclick = () => go(b.dataset.go)));
  $$('[data-learn]').forEach(b => (b.onclick = () => go('#/deck/' + encodeURIComponent(b.dataset.learn))));
  $$('.deckchip').forEach(b => (b.onclick = () => go('#/deck/' + encodeURIComponent(b.dataset.deck))));

  const feedEl = $('#feed');
  const secs = $$('.short[data-i]', feedEl);
  const blobs = [];
  let muted = SHORTS.pref('muted', false);
  let speed = SHORTS.pref('speed', 1);
  let active = null;
  const seenSent = new Set();

  function load(sec) {
    const v = $('video', sec);
    if (!v.src) v.src = v.dataset.src;
    return v;
  }
  function applyPrefs(v) {
    v.muted = muted; v.playbackRate = speed;
    secs.forEach(s => {
      $('[data-mute]', s).innerHTML = `${muted ? '🔇' : '🔊'}<small>${muted ? 'Stumm' : 'Ton'}</small>`;
      $('[data-speed]', s).innerHTML = `⏩<small>${speed}×</small>`;
    });
  }
  async function play(sec) {
    const v = load(sec);
    applyPrefs(v);
    try { await v.play(); }
    catch (e) {
      if (e && e.name === 'NotAllowedError' && !v.muted) {
        // Autoplay mit Ton blockiert → stumm starten, Ton per Tipp
        muted = true; applyPrefs(v);
        try { await v.play(); toast('🔇 Tippe auf 🔇 für Ton'); } catch { /* bleibt pausiert */ }
      }
    }
    sec.classList.toggle('paused', v.paused);
  }
  function activate(sec) {
    if (active === sec) return;
    if (active) { const v = $('video', active); v.pause(); }
    active = sec;
    play(sec);
    // nächstes Video vorladen
    const next = sec.nextElementSibling;
    if (next && next.dataset.i) load(next);
  }

  secs.forEach(sec => {
    const v = $('video', sec), it = items[+sec.dataset.i], bar = $('.seek i', sec);
    // Fallback: manche WebViews spielen eingebettete Videos nur als Blob ab
    v.addEventListener('error', async () => {
      if (v.dataset.blob) return;
      v.dataset.blob = '1';
      try {
        const url = URL.createObjectURL(await (await fetch(v.dataset.src)).blob());
        blobs.push(url); v.src = url;
        if (active === sec) play(sec);
      } catch { sec.classList.add('broken'); }
    });
    v.addEventListener('timeupdate', () => {
      if (!v.duration) return;
      bar.style.width = (v.currentTime / v.duration * 100) + '%';
      if (v.currentTime / v.duration > 0.85 && !seenSent.has(it.id)) {
        seenSent.add(it.id);
        call('short_seen', { id: it.id }).catch(() => {});
      }
    });
    v.addEventListener('ended', () => {
      const next = sec.nextElementSibling;
      if (SHORTS.pref('autonext', true) && next) setTimeout(() => active === sec && next.scrollIntoView({ behavior: 'smooth' }), 700);
      else { v.currentTime = 0; sec.classList.add('paused'); }
    });
    v.addEventListener('play', () => sec.classList.remove('paused'));
    v.addEventListener('pause', () => sec.classList.add('paused'));

    // Tippen = Pause/Weiter, Doppeltippen = merken
    let lastTap = 0, tapTimer = null;
    $('.tapzone', sec).addEventListener('click', () => {
      const t = Date.now();
      if (t - lastTap < 300) {
        clearTimeout(tapTimer); lastTap = 0;
        if (!it.liked) like();
        const h = $('.heart', sec); h.classList.remove('pop'); void h.offsetWidth; h.classList.add('pop');
        return;
      }
      lastTap = t;
      tapTimer = setTimeout(() => { if (v.paused) play(sec); else v.pause(); }, 260);
    });
    async function like() {
      it.liked = await safe(call('short_like', { id: it.id }));
      const b = $('[data-like]', sec);
      b.classList.toggle('on', it.liked);
      b.innerHTML = `${it.liked ? '❤️' : '🤍'}<small>Merken</small>`;
    }
    $('[data-like]', sec).onclick = like;
    $('[data-speed]', sec).onclick = () => {
      speed = SHORTS.speeds[(SHORTS.speeds.indexOf(speed) + 1) % SHORTS.speeds.length];
      SHORTS.setPref('speed', speed); applyPrefs(v); toast(`Tempo ${speed}×`, 1200);
    };
    $('[data-mute]', sec).onclick = () => {
      muted = !muted; SHORTS.setPref('muted', muted); applyPrefs(v);
      if (v.paused && active === sec) play(sec);
    };
    // Spulen über die Leiste
    const seek = $('.seek', sec);
    const seekTo = e => { const r = seek.getBoundingClientRect(); if (v.duration) v.currentTime = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * v.duration; };
    seek.addEventListener('pointerdown', e => { seek.setPointerCapture(e.pointerId); seekTo(e); seek.onpointermove = seekTo; });
    seek.addEventListener('pointerup', () => (seek.onpointermove = null));
  });

  const io = new IntersectionObserver(es => {
    es.forEach(e => {
      if (e.isIntersecting && e.intersectionRatio >= 0.6) activate(e.target);
      else if (e.target === active && e.intersectionRatio < 0.4) { $('video', e.target).pause(); active = null; }
    });
  }, { root: feedEl, threshold: [0, 0.4, 0.6, 1] });
  secs.forEach(s => io.observe(s));

  const onVis = () => { if (document.hidden && active) $('video', active).pause(); };
  document.addEventListener('visibilitychange', onVis);
  const onKey = e => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); feedEl.scrollBy({ top: (e.key === 'ArrowDown' ? 1 : -1) * feedEl.clientHeight, behavior: 'smooth' }); }
    if (e.key === ' ' && active) { e.preventDefault(); const v = $('video', active); v.paused ? play(active) : v.pause(); }
  };
  document.addEventListener('keydown', onKey);

  onLeave(() => {
    io.disconnect();
    document.removeEventListener('visibilitychange', onVis);
    document.removeEventListener('keydown', onKey);
    secs.forEach(s => { const v = $('video', s); v.pause(); v.removeAttribute('src'); v.load(); });
    blobs.forEach(u => URL.revokeObjectURL(u));
    document.body.classList.remove('shortsmode');
  });
}
