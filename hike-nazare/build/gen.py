import xml.etree.ElementTree as ET
import json, math, os, re

# Paths are derived from this file's location: build/ sits inside the page folder.
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)                        # static/hike-nazare
GPX_NAME = "caminho-da-nazare.gpx"
GPX = os.path.join(SRC, "gpx", GPX_NAME)
STAYS_TXT = os.path.join(SRC, "accomadation.txt")
TRAVEL_TXT = os.path.join(SRC, "transportation.txt")
TPL = os.path.join(HERE, "template.html")
OUT = os.path.join(SRC, "index.html")

NS = {"g": "http://www.topografix.com/GPX/1/1"}

def hav(a, b):
    R = 6371000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp = p2 - p1
    dl = math.radians(b[1] - a[1])
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(h))

# ---------------------------------------------------------------- route
root = ET.parse(GPX).getroot()
routes, order = {}, []
for r in root.findall("g:rte", NS):
    name = r.find("g:name", NS).text.strip()
    routes[name] = [
        [round(float(p.get("lat")), 5), round(float(p.get("lon")), 5),
         round(float(p.find("g:ele", NS).text), 1)]
        for p in r.findall("g:rtept", NS)
    ]
    order.append(name)
print("GPX routes:", order)

# The file stores some routes in reverse walking order; chain each onto the
# growing path by whichever endpoint is nearer the current tail.
path = list(routes[order[0]])
for name in order[1:]:
    seg = routes[name]
    d_fwd, d_rev = hav(path[-1], seg[0]), hav(path[-1], seg[-1])
    if d_rev < d_fwd:
        seg = seg[::-1]
        print(f"  {name}: reversed ({d_fwd/1000:.2f} km vs {d_rev/1000:.2f} km to tail)")
    if hav(path[-1], seg[0]) < 1:
        seg = seg[1:]
    path.extend(seg)

cum = [0.0]
for i in range(1, len(path)):
    cum.append(cum[-1] + hav(path[i-1], path[i]))
total = cum[-1]
print(f"merged: {len(path)} pts, {total/1000:.1f} km")

# ---------------------------------------------------------------- stays
def parse_stays(p):
    """One stay per line, in trip order. No dates are read or emitted - the
    page deliberately carries none."""
    out = []
    for raw in open(p, encoding="utf-8"):
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        m = re.match(r"^(.+?),\s*Latitude\s*([-\d.]+),"
                     r"\s*Longitude\s*([-\d.]+),\s*(\S+)$", raw)
        if not m:
            raise SystemExit(f"could not parse line:\n  {raw}")
        blob, lat, lon, url = m.groups()
        parts = [x.strip() for x in blob.split(",")]
        name = parts[0]
        # ...NAME, <address parts>, Portugal, TOWN, PT
        try:
            c = parts.index("Portugal")
            addr = ", ".join(parts[1:c])
            town = parts[c + 1] if len(parts) > c + 1 else ""
        except ValueError:
            addr, town = ", ".join(parts[1:]), ""
        out.append({
            "name": name, "addr": addr, "town": town, "url": url,
            "lat": float(lat), "lon": float(lon),
        })
    return out            # file order is trip order; do not sort

stays = parse_stays(STAYS_TXT)
print(f"\n{len(stays)} accommodations from {os.path.basename(STAYS_TXT)}:")

# The earliest stay is the night before setting off; each later one marks the
# end of a walking day, placed at the route's closest approach to it.
splits = []
for i, s in enumerate(stays):
    near = min(range(len(path)), key=lambda j: hav([path[j][0], path[j][1]], [s["lat"], s["lon"]]))
    off = hav([path[near][0], path[near][1]], [s["lat"], s["lon"]])
    s["off"] = round(off)
    if i == 0:
        s["role"] = "start"
        s["km"] = 0.0
        print(f"  {s['name']}  -> before the walk, {off:.0f} m from the start")
    else:
        s["role"] = "overnight"
        s["km"] = round(cum[near] / 1000, 1)
        splits.append(near)
        print(f"  {s['name']}  -> end of day {i}, "
              f"{cum[near]/1000:.1f} km in, {off:.0f} m off-route")
    if off > 2000:
        print(f"     !! {off/1000:.1f} km off the route - check the coordinates")

# ---------------------------------------------------------------- travel
def parse_travel(p):
    """when, mode, From - To, 18h00 > 20h40, <maps url> - one leg per line.
    Times are clock times only; no dates are read or emitted."""
    if not os.path.exists(p):
        return []
    out = []
    for raw in open(p, encoding="utf-8"):
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        m = re.match(r"^(.+?),\s*Latitude\s*([-\d.]+),"
                     r"\s*Longitude\s*([-\d.]+),\s*(\S+)$", raw)
        if not m:
            raise SystemExit(f"could not parse travel line:\n  {raw}")
        head, tlat, tlon, url = m.groups()
        parts = [x.strip() for x in head.split(",")]
        if len(parts) < 5:
            raise SystemExit(f"expected 'when, mode, from - to, times, terminal' in:\n  {raw}")
        when, mode, leg, times, terminal = parts[0], parts[1], parts[2], parts[3], parts[4]

        m = re.match(r"^(.+?)\s*-\s*(.+)$", leg)
        if not m:
            raise SystemExit(f"could not read 'From - To' from:\n  {raw}")
        frm, to = m.group(1).strip(), m.group(2).strip()

        def clock(t):
            g = re.match(r"^(\d{1,2})h(\d{2})m?$", t.strip())
            if not g:
                raise SystemExit(f"could not read time {t!r} in:\n  {raw}")
            return int(g.group(1)), int(g.group(2))

        tparts = [x for x in re.split(r">", times) if x.strip()]
        if len(tparts) != 2:
            raise SystemExit(f"expected 'depart > arrive' in:\n  {raw}")
        (h1, m1), (h2, m2) = clock(tparts[0]), clock(tparts[1])
        mins = (h2 * 60 + m2) - (h1 * 60 + m1)
        if mins < 0:
            mins += 24 * 60                      # crosses midnight
        out.append({
            "when": when, "mode": mode, "from": frm, "to": to,
            "depart": f"{h1:02d}:{m1:02d}", "arrive": f"{h2:02d}:{m2:02d}",
            "duration": (f"{mins//60}h {mins%60:02d}m" if mins % 60 else f"{mins//60}h"),
            "terminal": terminal, "lat": float(tlat), "lon": float(tlon),
            "url": url,
        })
    return out

travel = parse_travel(TRAVEL_TXT)

# A terminal far from the walk (Porto is ~170 km north) still gets a marker, but
# must not stretch the map's initial bounds or the route becomes a squiggle.
NEAR_M = 25000
for t in travel:
    near_i = min(range(len(path)),
                 key=lambda j: hav([path[j][0], path[j][1]], [t["lat"], t["lon"]]))
    t["off"] = round(hav([path[near_i][0], path[near_i][1]], [t["lat"], t["lon"]]))
    t["near"] = t["off"] <= NEAR_M

print(f"\n{len(travel)} travel legs from {os.path.basename(TRAVEL_TXT)}:")
for t in travel:
    where = (f"{t['off']} m from the route" if t["near"]
             else f"{t['off']/1000:.0f} km away - marker only, not framed")
    print(f"  {t['from']} -> {t['to']}  {t['mode']}  "
          f"{t['depart']} > {t['arrive']} ({t['duration']})  [{t['when']}]")
    print(f"     terminal: {t['terminal']}  ({where})")

# ---------------------------------------------------------------- days
edges = [0] + splits + [len(path) - 1]
days = []
for i in range(len(edges) - 1):
    a, b = edges[i], edges[i+1]
    up = sum(max(0, path[j+1][2] - path[j][2]) for j in range(a, b))
    down = sum(max(0, path[j][2] - path[j+1][2]) for j in range(a, b))
    days.append({"from": a, "to": b, "dist": cum[b] - cum[a], "up": up, "down": down})
print(f"\n{len(days)} walking days:")
for i, d in enumerate(days, 1):
    print(f"  Day {i}: {d['dist']/1000:5.1f} km  +{d['up']:.0f}/-{d['down']:.0f} m  "
          f"idx {d['from']}..{d['to']}")

# ---------------------------------------------------------------- emit
tpl = open(TPL, encoding="utf-8").read()
subs = {
    "/*__DATA__*/":  json.dumps(path, separators=(",", ":")),
    "/*__SPLITS__*/": json.dumps(splits),
    "/*__STAYS__*/": json.dumps(stays, ensure_ascii=False, separators=(",", ":")),
    "/*__TRAVEL__*/": json.dumps(travel, ensure_ascii=False, separators=(",", ":")),
    "/*__GPXNAME__*/": json.dumps(GPX_NAME, ensure_ascii=False),
}
for k, v in subs.items():
    assert k in tpl, f"missing {k} in template"
    tpl = tpl.replace(k, v)
# privacy guard: the page must carry no dates
leaks = re.findall(r"\b\d{2}-\d{2}-\d{4}\b|\b\d{4}-\d{2}-\d{2}\b"
                   r"|\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4}\b", tpl)
if leaks:
    raise SystemExit(f"refusing to write: date-like strings in output: {sorted(set(leaks))}")
print("privacy check: no dates in output")

open(OUT, "w", encoding="utf-8").write(tpl)
print(f"\nwrote {OUT} ({len(tpl.encode())/1024:.0f} KB)")
