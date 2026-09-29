"""Read-only HTML twin of dashboard.md: every pool row in one filterable table. It polls the watcher's beat.js and
reloads when dashboard.html is rewritten."""
import time
from html import escape

OURS = "Δw '26–'27 ours"

STYLE = """
:root{--ink:#e6e8ee;--mute:#949cab;--line:#2d323c;--row:#252932;--bg:#15171c;--card:#1c1f26;--raise:#242831;
--hover:#232833;--bid:#4cc38a;--bidbg:#1d3a2c;--warn:#e0a458;--warnbg:#3a2c1a;--bad:#ff7b72;--badbg:#3d1f22;
--focus:#5b9dff;--dim:#6b7280}
*{box-sizing:border-box}
html{background:var(--bg)}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.4 -apple-system,BlinkMacSystemFont,"SF Pro Text",
system-ui,sans-serif;font-variant-numeric:tabular-nums;-webkit-font-smoothing:antialiased}
header{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--line);padding:14px 24px;
box-shadow:0 6px 18px #0000004d}
.stats{display:flex;gap:10px;flex-wrap:wrap;align-items:stretch}
.stat{background:var(--raise);border:1px solid var(--line);border-radius:10px;padding:8px 14px;min-width:96px}
.stat b{display:block;font-size:22px;font-weight:650;letter-spacing:-.01em;color:#f3f4f7}
.stat span{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute)}
.stat.nom{flex:1;min-width:220px}.stat.nom b{font-size:18px}
.stat.warn{background:var(--warnbg);border-color:var(--warn)}.stat.warn b{font-size:18px;color:var(--warn)}
.live{display:flex;align-items:center;gap:8px}.live i{width:10px;height:10px;border-radius:50%;background:var(--dim)}
.live.on i{background:var(--bid);box-shadow:0 0 0 4px #4cc38a2e}
.live.down{background:var(--badbg);border-color:#6e2b2e;color:var(--bad)}
.live.down i{background:var(--bad);box-shadow:0 0 0 4px #ff7b722e}.live.down span,.live.down b{color:var(--bad)}
.live b{font-size:15px}
#q{margin-top:12px;width:100%;font:500 20px/1.2 inherit;padding:12px 16px;border:2px solid var(--line);
border-radius:12px;background:var(--bg);color:var(--ink);outline:none;caret-color:var(--focus)}
#q::placeholder{color:#6f7787}
#q:focus{border-color:var(--focus);box-shadow:0 0 0 4px #5b9dff40}
#hits{display:flex;gap:12px;flex-wrap:wrap}#hits:not(:empty){margin-top:12px}
.hit{flex:1;min-width:260px;max-width:420px;background:var(--raise);border:1px solid var(--line);border-radius:14px;
padding:14px 18px;border-left:8px solid var(--dim)}
.hit.bid{border-color:#2f5e45;border-left-color:var(--bid);background:var(--bidbg)}.hit.sold{opacity:.55}
.hit h2{margin:0 0 4px;font-size:17px;color:#f3f4f7}.hit .v{font-size:34px;font-weight:700;letter-spacing:-.02em}
.hit.bid .v{color:#5fd49b}.hit.pass .v{color:var(--mute)}.hit .m{color:var(--mute);font-size:13px}
main{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:20px;padding:16px 24px 40px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.panel h3{margin:0;padding:10px 14px;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute);
border-bottom:1px solid var(--line)}
aside,main>.panel{align-self:start}aside{display:flex;flex-direction:column;gap:16px}
table{width:100%;border-collapse:collapse}
td,th{padding:6px 12px;white-space:nowrap;text-align:right}td:first-child,th:first-child{text-align:left}
thead th{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--mute);font-weight:600;
background:var(--card);border-bottom:1px solid var(--line)}
tbody tr{border-bottom:1px solid var(--row)}tbody tr:hover{background:var(--hover)}
tr.sec th{text-align:left;background:var(--raise);color:var(--mute);font-size:11px;letter-spacing:.06em;
text-transform:uppercase;padding:8px 12px}
tr.bid td:first-child{font-weight:600}tr.bid td.cap{color:#5fd49b;font-weight:700;background:var(--bidbg)}
td.cap{font-weight:600;color:#f3f4f7}tr.pass td.cap{color:var(--mute);font-weight:400}
tr.sold td,tr.sold s{color:var(--dim)}
.side td{padding:5px 14px;font-size:13px}
.empty{padding:10px 14px;color:var(--mute);font-size:13px}
"""

SCRIPT = """
const q = document.getElementById('q'), hits = document.getElementById('hits');
const rows = [...document.querySelectorAll('#pool tbody tr')];
const fold = t => t.normalize('NFD').replace(/\\p{Diacritic}/gu, '').toLowerCase();
function card(tr) {
  const d = tr.dataset, v = d.state === 'bid' ? 'bid to $' + d.cap : d.state === 'sold' ? d.sold : 'PASS';
  const m = d.state === 'sold' ? '' : `Mkt $${d.mkt} · Score ${d.score || '–'} · ΔP ${d.dp || '–'}`;
  return `<div class="hit ${d.state}"><h2>${d.name}</h2><div class="v">${v}</div>
<div class="m">${m}</div></div>`;
}
function apply() {
  const f = fold(q.value.trim()), shown = [];
  for (const tr of rows) {
    if (tr.classList.contains('sec')) { tr.hidden = !!f; continue; }
    tr.hidden = !fold(tr.cells[0].textContent).includes(f);
    if (!tr.hidden) shown.push(tr);
  }
  hits.innerHTML = f && shown.length <= 3 ? shown.map(card).join('') : '';
}
function set(v) { q.value = v; history.replaceState(null, '', '#' + encodeURIComponent(v)); apply(); }
let typed = 0, due = false;
const typing = () => document.activeElement === q && Date.now() - typed < 2000;
function reload() {
  if (typing()) return setTimeout(reload, 300);
  sessionStorage.setItem('y', scrollY); location.reload();
}
q.value = decodeURIComponent(location.hash.slice(1));
q.setSelectionRange(q.value.length, q.value.length);
q.addEventListener('input', () => { typed = Date.now(); set(q.value); });
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { set(''); q.focus(); }
  else if (document.activeElement !== q && !e.metaKey && !e.ctrlKey && (e.key === '/' || e.key.length === 1)) {
    q.focus(); if (e.key === '/') e.preventDefault();
  }
});
apply();
scrollTo(0, +sessionStorage.getItem('y') || 0);
const live = document.getElementById('live');
function show(cls, head, sub) {
  live.className = 'stat live ' + cls; live.querySelector('b').textContent = head;
  live.querySelector('span').textContent = sub;
}
const ago = () => { const s = Math.round(Date.now() / 1000 - GEN); return s < 90 ? s + 's ago' : Math.round(s / 60) + 'm ago'; };
function beat() {
  document.getElementById('beat')?.remove();
  const tag = Object.assign(document.createElement('script'), {id: 'beat', src: `beat.js?_=${Date.now()}`});
  tag.onload = () => {
    const b = window.BEAT;
    if (b.v - GEN > 1 && !due) { due = true; reload(); }
    if (Date.now() / 1000 - b.t > 15) show('down', 'watcher down', 'no Sheet read in ' + Math.round(Date.now() / 1000 - b.t) + 's');
    else show('on', 'live', 'updated ' + ago());
  };
  tag.onerror = () => show('', 'not live', 'updated ' + ago());
  document.head.append(tag);
}
beat(); setInterval(beat, 2000);
"""


def num(x, sign=False):
    return '' if x in (None, '') else f'{float(x):+.2f}' if sign else x


def pool_row(s, n, cap, gap):
    r = s.by_name[n]
    if n in s.sold:
        o, x = s.sold[n]
        return (f'<tr class="sold" data-name="{escape(n)}" data-state="sold" data-sold="{escape(f"sold {o} ${x}")}"><td><s>{escape(n)}</s> '
                f'{escape(o)} ${escape(str(x))}</td>' + '<td></td>' * 7 + '</tr>')
    c = cap(s, n) if n in s.card else None
    state = 'bid' if c and c > 0 else 'pass'
    score, dp = num(r.get('score')), num(r.get('dPtitle'), sign=True)
    cells = [('cap', c if c is not None else 'pass'), ('', s.live[n]), ('', score), ('', dp),
             ('', f'{gap(s, n):+d}' if c is not None else ''), ('', r.get('BASE', '')), ('', num(r.get(OURS), sign=True))]
    tds = ''.join(f'<td class="{k}">{escape(str(x))}</td>' if k else f'<td>{escape(str(x))}</td>' for k, x in cells)
    data = f'data-name="{escape(n)}" data-state="{state}" data-cap="{c or 0}" data-mkt="{s.live[n]}" data-score="{score}" data-dp="{dp}"'
    return f'<tr class="{state}" {data}><td>{escape(n)}</td>{tds}</tr>'


def section(label):
    return f'<tr class="sec"><th colspan="8">{label}</th></tr>'


def render(s, log, room, cap, gap):
    """Full page: header stats and filter, then the card by Score, the rest of the pool by live Market$ and sold rows
    struck, with rivals and the last 8 sales beside it."""
    left, spots, hard = s.us
    targets = [n for n in s.card if n not in s.not_in_pool]
    rest = sorted((r['name'] for r in s.values if r['name'] not in s.not_in_pool and r['name'] not in s.card),
                  key=lambda n: -s.live[n])
    sold = [n for n, _, _ in log[::-1] if n in s.by_name]
    body = ''.join(x for label, names in (('Targets · by Score', targets), ('Pass · rest of the pool', rest),
                                         ('Sold', sold)) if names
                   for x in [section(label)] + [pool_row(s, n, cap, gap) for n in names])
    rivals = ''.join(f'<tr><td>{escape(o)}</td><td>{t[2]}</td><td>${t[0]}</td><td>{t[1]}</td></tr>'
                     for o, t in s.rivals)
    sales = ''.join(f'<tr><td>{escape(p)}</td><td>{escape(t)}</td><td>${escape(str(x))}</td></tr>'
                    for p, t, x in log[::-1][:8]) or '<tr><td class="empty">No sales yet</td></tr>'
    head = ''.join(f'<th>{h}</th>' for h in ('Player', 'Cap', 'Mkt', 'Score', 'ΔP', 'Gap', 'BASE', 'Δw ours'))
    heat = room.removeprefix('room ')
    heat = f'waiting · {heat[2:]} sales' if heat.startswith('?') else heat
    stat = lambda v, k, c='': f'<div class="stat {c}"><b>{v}</b><span>{k}</span></div>'  # noqa: E731
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Auction · ${left} · {spots} spots</title>
<meta name="color-scheme" content="dark"><style>{STYLE}</style></head><body>
<header><div class="stats">{stat(f'${left}', '$ left')}{stat(spots, 'spots')}{stat(f'${hard}', 'max bid')}
{stat(escape(s.nominee or '–'), 'nominate', 'nom')}{stat(escape(heat), 'room heat')}
{''.join(stat(escape(f'WARN {w}'), 'fix the Sheet or aliases.tsv', 'warn') for w in s.warns)}
<div class="stat live" id="live"><i></i><div><b>not live</b><span>updated {time.strftime('%-I:%M:%S')}</span></div></div></div>
<input id="q" placeholder="Player up? Type a name   ( / to focus · Esc to clear )" autofocus autocomplete="off"
spellcheck="false"><div id="hits"></div></header>
<main><div class="panel"><table id="pool"><thead><tr>{head}</tr></thead><tbody>
{body}
</tbody></table></div>
<aside><div class="panel"><h3>Rivals · max bid · $ left · spots</h3><table class="side">{rivals}</table></div>
<div class="panel"><h3>Last sales</h3><table class="side">{sales}</table></div></aside></main>
<script>const GEN = {time.time():.3f};{SCRIPT}</script></body></html>
"""
