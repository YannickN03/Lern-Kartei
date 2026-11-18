// Mini-Markdown für Karten: ```Code```, `code`, **fett**, ==markiert==, Listen, Tabellen (| a | b |).
const MD = (() => {
  const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const inline = s => esc(s)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>')
    .replace(/==([^=]+)==/g, '<mark>$1</mark>');

  function render(src) {
    const out = [];
    const lines = String(src || '').replace(/\r/g, '').split('\n');
    let i = 0;
    while (i < lines.length) {
      const l = lines[i];
      if (l.trimStart().startsWith('```')) {
        const buf = [];
        i++;
        while (i < lines.length && !lines[i].trimStart().startsWith('```')) buf.push(lines[i++]);
        i++;
        out.push(`<pre><code>${esc(buf.join('\n'))}</code></pre>`);
        continue;
      }
      if (/^\s*\|/.test(l)) {
        const rows = [];
        while (i < lines.length && /^\s*\|/.test(lines[i])) rows.push(lines[i++]);
        const cells = r => r.trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim());
        const body = rows.filter(r => !/^\s*\|[\s:-|]+\|?\s*$/.test(r));
        const head = rows.length > 1 && /^\s*\|[\s:-|]+\|?\s*$/.test(rows[1]);
        out.push('<table>' + body.map((r, n) => {
          const tag = head && n === 0 ? 'th' : 'td';
          return '<tr>' + cells(r).map(c => `<${tag}>${inline(c)}</${tag}>`).join('') + '</tr>';
        }).join('') + '</table>');
        continue;
      }
      if (/^\s*([-•*]|\d+\.)\s+/.test(l)) {
        const ordered = /^\s*\d+\./.test(l);
        const items = [];
        while (i < lines.length && /^\s*([-•*]|\d+\.)\s+/.test(lines[i])) items.push(lines[i++].replace(/^\s*([-•*]|\d+\.)\s+/, ''));
        const t = ordered ? 'ol' : 'ul';
        out.push(`<${t}>${items.map(x => `<li>${inline(x)}</li>`).join('')}</${t}>`);
        continue;
      }
      if (!l.trim()) { i++; continue; }
      const para = [];
      while (i < lines.length && lines[i].trim() && !/^\s*(```|\||([-•*]|\d+\.)\s)/.test(lines[i])) para.push(inline(lines[i++]));
      out.push(`<p>${para.join('<br>')}</p>`);
    }
    return out.join('');
  }

  // Zerlegt alle Textknoten in Wort-Spans (data-i = laufender Wortindex) für Markierungen.
  function wrapWords(root, marks) {
    const map = new Map((marks || []).map(([i, c]) => [i, c]));
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    let idx = 0;
    for (const n of nodes) {
      const parts = n.nodeValue.split(/(\s+)/);
      if (parts.length === 1 && !parts[0]) continue;
      const frag = document.createDocumentFragment();
      for (const p of parts) {
        if (!p) continue;
        if (/^\s+$/.test(p)) { frag.appendChild(document.createTextNode(p)); continue; }
        const s = document.createElement('span');
        s.className = 'w';
        s.dataset.i = idx;
        if (map.has(idx)) s.classList.add('m' + map.get(idx));
        s.textContent = p;
        frag.appendChild(s);
        idx++;
      }
      n.parentNode.replaceChild(frag, n);
    }
  }

  return { render, wrapWords, esc };
})();
