'use strict';
const $ = id => document.getElementById(id);
const escapeHtml = value => String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
let snapshot, selected = null, direction = 'callers', related = new Set(), requestNumber = 0;
async function api(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Request failed');
  return data;
}
function status(message) {$('status').textContent = message;}
function codeBlock(text, line) {
  return '<pre class="code">' + escapeHtml(text.split('\n').map((s, i) => String(line + i).padStart(4) + '  ' + s).join('\n')) + '</pre>';
}
async function load(run) {
  snapshot = await api('/api/snapshot' + (run ? '?run=' + run : ''));
  selected = null; related = new Set(); requestNumber++;
  $('detail-title').textContent = 'Evidence explorer';
  $('detail').innerHTML = '<div class="empty"><span>↖</span><h3>Start with a connection</h3><p>Выбери функцию на карте или задай вопрос.</p></div>';
  $('results-panel').hidden = true;
  $('repo-name').textContent = snapshot.name;
  $('run-label').textContent = 'SNAPSHOT ' + snapshot.run_id;
  for (const [id, count] of [['files', snapshot.file_count], ['symbols', snapshot.symbols.length], ['edges', snapshot.edges.length], ['documents', snapshot.documents.length]]) $(id).textContent = count;
  $('coverage-label').textContent = `Analysis coverage · ${snapshot.unresolved.length} unresolved calls · ${snapshot.warnings.length} warnings`;
  $('warnings').innerHTML = snapshot.warnings.map(w => '<div class="warning">' + escapeHtml(w.path + ': ' + w.message) + '</div>').join('');
  $('unresolved').innerHTML = snapshot.unresolved.slice(0, 100).map(e => '<div class="warning">' + escapeHtml(e.source + ':' + e.line + ' → ' + e.expression + ' · ' + e.reason) + '</div>').join('') + (snapshot.unresolved.length > 100 ? '<p>Showing the first 100; the full list is available in the JSON snapshot.</p>' : '');
  renderGraph();
}
function renderGraph() {
  // Deterministic module columns. Large repositories get a focused subgraph.
  const all = [...snapshot.symbols].sort((a,b) => a.path.localeCompare(b.path) || a.line-b.line);
  let nodes = all;
  if (all.length > 100) {
    nodes = selected ? all.filter(s => s.id === selected || related.has(s.id)).slice(0,100) : all.slice(0,100);
  }
  const groups = [...new Set(nodes.map(s => s.path))];
  const columns = Math.min(groups.length, 3) || 1;
  const width = Math.max(470, columns * 180);
  const positions = new Map();
  let maxY = 60;
  const heights = Array(columns).fill(40);
  let headings = '';
  groups.forEach((path, index) => {
    const column = index % columns, x = column * width / columns + 12, y = heights[column];
    headings += `<text x="${x}" y="${y}" fill="#9299aa" font-size="8" font-family="monospace">${escapeHtml(path.length > 24 ? '…' + path.slice(-23) : path)}</text>`;
    const members = nodes.filter(s => s.path === path);
    members.forEach((s,i) => positions.set(s.id, {x,y:y+18+i*44}));
    heights[column] += 42 + members.length*44;
    maxY = Math.max(maxY, heights[column]);
  });
  const lines = snapshot.edges.filter(e=>positions.has(e.source)&&positions.has(e.target)).map(e=>{
    const a=positions.get(e.source),b=positions.get(e.target), highlight=(e.source===selected||related.has(e.source))&&(e.target===selected||related.has(e.target));
    const x1=a.x+69,y1=a.y+26,x2=b.x+69,y2=b.y;
    return `<path class="edge ${highlight?'highlight':''}" d="M${x1},${y1} C${x1+25},${y1+18} ${x2-25},${y2-18} ${x2},${y2}" marker-end="url(#arrow)"/>`;
  }).join('');
  const rectangles = nodes.map(s=>{
    const {x,y}=positions.get(s.id); const label=s.qualname.length>20?s.qualname.slice(0,18)+'…':s.qualname;
    return `<g class="node ${s.id===selected?'selected':related.has(s.id)?'related':''}" data-symbol="${escapeHtml(s.id)}" tabindex="0" role="button" aria-label="${escapeHtml(s.qualname)}"><title>${escapeHtml(s.id)}</title><rect x="${x}" y="${y}" rx="6" width="142" height="27"/><text x="${x+9}" y="${y+17}">${escapeHtml(label)}</text></g>`;
  }).join('');
  $('graph').innerHTML=`${all.length>100?'<p class="hint">Showing up to 100 symbols. Search to focus the graph.</p>':''}<svg viewBox="0 0 ${width} ${maxY}" role="group" aria-label="Call graph"><defs><marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="#b4a5cf"/></marker></defs>${headings}${lines}${rectangles}</svg>`;
}
async function selectSymbol(id) {
  const ticket = ++requestNumber;
  const data = await api('/api/impact?' + new URLSearchParams({symbol:id,direction,run:snapshot.run_id}));
  if(ticket !== requestNumber) return;
  selected=id; related=new Set(data.affected.map(a=>a.symbol.id)); renderGraph();
  $('detail-title').textContent=data.symbol.qualname;
  $('detail').innerHTML=`<div class="source-path">${escapeHtml(data.symbol.path)} : ${data.symbol.line}–${data.symbol.end_line}</div>${codeBlock(data.symbol.source,data.symbol.line)}<div class="detail-tabs"><button data-direction="callers" class="${direction==='callers'?'active':''}">← Affected callers</button><button data-direction="callees" class="${direction==='callees'?'active':''}">Calls →</button></div><ul class="evidence-list">${data.affected.map(a=>`<li><button class="symbol-link" data-symbol="${escapeHtml(a.symbol.id)}">${escapeHtml(a.symbol.qualname)}</button><small>${a.distance} hop(s) · ${escapeHtml(a.evidence.map(e=>e.source+':'+e.line+' → '+e.expression).join(' / '))}</small></li>`).join('')||'<li>No resolved references in this direction.</li>'}</ul><h3>Related documentation</h3><ul class="evidence-list">${data.documents.map(d=>`<li><button class="symbol-link" data-doc="${escapeHtml(d.id)}">${escapeHtml(d.title)}</button><small>${escapeHtml(d.path)}:${d.line} · retrieval suggestion</small></li>`).join('')||'<li>No matching sections.</li>'}</ul><p class="hint">${escapeHtml(data.caveat)}</p>`;
}
function selectDocument(id) {
  const doc=snapshot.documents.find(d=>d.id===id);
  if(!doc)return;
  requestNumber++;
  $('detail-title').textContent=doc.title;
  $('detail').innerHTML=`<div class="source-path">${escapeHtml(doc.path)} : ${doc.line}–${doc.end_line}</div>${codeBlock(doc.text,doc.line)}<p class="hint">Original Markdown, displayed as text. Document content is never executed.</p>`;
}
async function search() {
  const query=$('query').value.trim();
  if(!query){status('Поле поиска пустое. Напиши вопрос или нажми на пример под строкой поиска.');$('query').focus();return;}
  const data=await api('/api/search?'+new URLSearchParams({q:query,method:$('method').value,run:snapshot.run_id}));
  $('results-panel').hidden=false; $('results-count').textContent=data.length+' MATCHES';
  $('results').innerHTML=data.map(r=>`<button class="result" ${r.kind==='code'?'data-symbol':'data-doc'}="${escapeHtml(r.id)}"><span class="badge">${r.kind.toUpperCase()}</span><span class="result-title">${escapeHtml(r.title)}</span><div class="result-meta">${escapeHtml(r.path)}:${r.line} · score ${r.score.toFixed(2)} · ${escapeHtml(r.matched_terms.join(', '))}</div><div class="result-excerpt">${escapeHtml(r.text.slice(0,350))}</div></button>`).join('')||'<p class="hint">Нет совпадений. Попробуй имя функции или английские термины. Поиск не генерирует ответ при отсутствии доказательств.</p>';
  status('');
  if(data[0]) {if(data[0].kind==='code')await selectSymbol(data[0].id);else selectDocument(data[0].id);}
}
async function history() {
  const runs=await api('/api/runs'); $('history-panel').hidden=false;
  $('runs').innerHTML=runs.map(r=>`<div class="run-row"><span>#${r.id} · ${escapeHtml(r.created_at)} · ${r.file_count} files</span><div><button class="button" data-run="${r.id}">Open</button> <button class="button" data-compare="${r.id}">Compare to current</button></div></div>`).join('');
  $('history-panel').scrollIntoView({behavior:'smooth'});
}
async function compareRun(before) {
  const data=await api('/api/compare?'+new URLSearchParams({before,run:snapshot.run_id}));
  $('changes').innerHTML='<h3>'+data.count+' changed symbols</h3>'+data.changes.map(c=>`<div class="change-row"><span class="badge">${c.status}</span>${escapeHtml(c.id)}<p>${c.impact.affected.length} current/context callers · ${c.previous_callers.length} previous callers</p><p>Review: ${escapeHtml(c.impact.documents.map(d=>d.path+':'+d.line).join(', ')||'No documentation match')}</p></div>`).join('')+'<p class="hint">'+escapeHtml(data.caveat)+'</p>';
}
function handleError(error){status(error.message);}
$('search-form').addEventListener('submit',event=>{event.preventDefault();search().catch(handleError);});
$('history').addEventListener('click',()=>history().catch(handleError));
$('overview').addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));
$('rescan').addEventListener('click',async()=>{
  $('rescan').disabled=true;status('Indexing source and documentation…');
  try{const result=await api('/api/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});await load(result.run_id);status('Snapshot '+result.run_id+' saved. Use Snapshot history to compare changes.');}
  catch(error){handleError(error);}finally{$('rescan').disabled=false;}
});
document.addEventListener('click',event=>{
  const el=event.target.closest('[data-symbol],[data-doc],[data-query],[data-direction],[data-run],[data-compare]');if(!el)return;
  if(el.dataset.symbol)selectSymbol(el.dataset.symbol).catch(handleError);
  else if(el.dataset.doc)selectDocument(el.dataset.doc);
  else if(el.dataset.query){$('query').value=el.dataset.query;search().catch(handleError);}
  else if(el.dataset.direction){direction=el.dataset.direction;if(selected)selectSymbol(selected).catch(handleError);}
  else if(el.dataset.run)load(el.dataset.run).catch(handleError);
  else if(el.dataset.compare)compareRun(el.dataset.compare).catch(handleError);
});
$('graph').addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){const el=event.target.closest('[data-symbol]');if(el){event.preventDefault();selectSymbol(el.dataset.symbol).catch(handleError);}}});
load().catch(handleError);
