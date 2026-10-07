// Renders every <figure class="gpx"> emitted by layouts/shortcodes/gpx.html:
// a Leaflet map of one or more routes plus distance / climb stats.

const NOISE_M = 3; // elevation changes smaller than this are treated as GPS noise
// One colour per file, cycling: the blog's tag colours from assets/sass/_base.scss.
const PALETTE = ['#0077c0', '#b85c00', '#2a7d45', '#7b2d8b'];

function haversine(a, b) {
  const R = 6371000;
  const p1 = a[0] * Math.PI / 180, p2 = b[0] * Math.PI / 180;
  const dp = p2 - p1, dl = (b[1] - a[1]) * Math.PI / 180;
  const h = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

// Returns { name, segs } where segs are arrays of [lat, lon, ele|null]. Tracks first;
// route-only files (e.g. Hiiker exports) have no <trkpt>, so fall back to <rtept>.
function parseGpx(text) {
  const doc = new DOMParser().parseFromString(text, 'application/xml');
  const groups = (parent, child) => [...doc.getElementsByTagName(parent)]
    .map(g => [...g.getElementsByTagName(child)].map(p => {
      const e = p.getElementsByTagName('ele')[0];
      const ele = e ? parseFloat(e.textContent) : NaN;
      return [parseFloat(p.getAttribute('lat')), parseFloat(p.getAttribute('lon')),
              Number.isFinite(ele) ? ele : null];
    }))
    .filter(s => s.length > 1);
  const trk = groups('trkseg', 'trkpt');
  const isTrk = trk.length > 0;
  const owner = doc.getElementsByTagName(isTrk ? 'trk' : 'rte')[0];
  const nameEl = owner && [...owner.children].find(c => c.localName === 'name');
  return { name: nameEl ? nameEl.textContent.trim() : '',
           segs: isTrk ? trk : groups('rte', 'rtept') };
}

// Climb with hysteresis: only commit a change once it exceeds NOISE_M.
function climb(eles) {
  let up = 0, down = 0, ref = null;
  for (const e of eles) {
    if (e == null) continue;
    if (ref == null) { ref = e; continue; }
    const d = e - ref;
    if (d >= NOISE_M) { up += d; ref = e; }
    else if (d <= -NOISE_M) { down -= d; ref = e; }
  }
  return { up, down };
}

function stats(segs) {
  // Distance does not bridge gaps between segments.
  let total = 0, up = 0, down = 0;
  for (const seg of segs) {
    for (let i = 1; i < seg.length; i++) total += haversine(seg[i - 1], seg[i]);
    const c = climb(seg.map(p => p[2]));
    up += c.up; down += c.down;
  }
  const eles = segs.flat().map(p => p[2]).filter(e => e != null);
  const hasEle = eles.length > 1;
  return { total, up, down, hasEle,
           min: hasEle ? Math.min(...eles) : 0, max: hasEle ? Math.max(...eles) : 0 };
}

const km = m => (m / 1000).toFixed(m < 10000 ? 2 : 1);
const m = v => Math.round(v).toLocaleString('en');

const esc = t => t.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

// Totals across every file; min/max only over files that have elevation.
function combine(list) {
  const withEle = list.filter(s => s.hasEle);
  return {
    total: list.reduce((a, s) => a + s.total, 0),
    up: list.reduce((a, s) => a + s.up, 0),
    down: list.reduce((a, s) => a + s.down, 0),
    hasEle: withEle.length > 0,
    min: Math.min(...withEle.map(s => s.min)),
    max: Math.max(...withEle.map(s => s.max)),
  };
}

function renderStats(el, s, tracks) {
  const parts = [`<b>${km(s.total)}</b> km`];
  if (s.hasEle) {
    parts.push(`<b>+${m(s.up)}</b> / <b>−${m(s.down)}</b> m`);
    parts.push(`${m(s.min)}–${m(s.max)} m elevation`);
  }
  let html = parts.join(' · ');
  // Several files: one row per file, its swatch matching the line on the map.
  if (tracks.length > 1) {
    html += '<ul class="gpx-legend">' + tracks.map(t =>
      `<li><span class="gpx-swatch" style="background:${t.color}"></span>` +
      `<span class="gpx-label">${esc(t.label)}</span>` +
      `<span>${km(t.stats.total)} km</span>` +
      (t.stats.hasEle ? `<span>+${m(t.stats.up)} / −${m(t.stats.down)} m</span>` : '') +
      '</li>').join('') + '</ul>';
  }
  el.innerHTML = html;
}

function renderMap(el, tracks) {
  const lines = tracks.map(t => t.segs.map(s => s.map(p => [p[0], p[1]])));
  // The view must be set before vector layers are added, or Leaflet's renderer
  // has no bounds yet and throws reading 'min'.
  const map = L.map(el, { scrollWheelZoom: false })
    .fitBounds(L.latLngBounds(lines.flat(2)), { padding: [16, 16] });
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);
  // Transparent overlay highlighting official waymarked hiking routes (GR, PR, …).
  L.tileLayer('https://tile.waymarkedtrails.org/hiking/{z}/{x}/{y}.png', {
    maxZoom: 18,
    opacity: 0.5,   // faded so our tracks stay the most prominent lines
    attribution: 'Trails &copy; <a href="https://hiking.waymarkedtrails.org">Waymarked Trails</a>',
  }).addTo(map);
  // White casing under every track first, so no track's casing covers another track.
  lines.flat().forEach(l => L.polyline(l, { color: '#fff', weight: 8, opacity: 0.9, interactive: false }).addTo(map));
  tracks.forEach((t, i) => lines[i].forEach(l => {
    const line = L.polyline(l, { color: t.color, weight: 4, opacity: 1 }).addTo(map);
    if (tracks.length > 1) line.bindTooltip(esc(t.label), { sticky: true });
  }));
  const firstSegs = tracks[0].segs, lastSegs = tracks[tracks.length - 1].segs;
  const first = firstSegs[0][0], last = lastSegs[lastSegs.length - 1].at(-1);
  const dot = (p, fill) => L.circleMarker([p[0], p[1]],
    { radius: 6, color: '#1d242b', weight: 2, fillColor: fill, fillOpacity: 1 }).addTo(map);
  dot(first, '#fafafa').bindTooltip('Start');
  dot(last, '#1d242b').bindTooltip('Finish');
}

async function init(fig) {
  const statsEl = fig.querySelector('.gpx-stats');   // absent with map-only=true
  const mapEl = fig.querySelector('.gpx-map');
  try {
    const tracks = await Promise.all(JSON.parse(fig.dataset.tracks).map(async (src, i) => {
      const file = decodeURIComponent(src.url.split('/').pop());
      const res = await fetch(src.url);
      if (!res.ok) throw new Error(`${file}: HTTP ${res.status}`);
      const { name, segs } = parseGpx(await res.text());
      if (!segs.length) throw new Error(`${file}: no track or route points`);
      return { segs, stats: stats(segs), label: src.label || name || file,
               color: PALETTE[i % PALETTE.length] };
    }));
    if (statsEl) renderStats(statsEl, combine(tracks.map(t => t.stats)), tracks);
    renderMap(mapEl, tracks);
  } catch (e) {
    const msg = `Could not load route (${e.message}).`;
    if (statsEl) statsEl.textContent = msg;
    else mapEl.innerHTML = `<p class="gpx-error">${esc(msg)}</p>`;
  }
}

const figs = document.querySelectorAll('figure.gpx');
if ('IntersectionObserver' in window) {
  const io = new IntersectionObserver(entries => entries.forEach(en => {
    if (en.isIntersecting) { io.unobserve(en.target); init(en.target); }
  }), { rootMargin: '300px' });
  figs.forEach(f => io.observe(f));
} else {
  figs.forEach(init);
}
