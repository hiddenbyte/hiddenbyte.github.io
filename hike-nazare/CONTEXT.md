# hike-nazare — context

Standalone page for a two-day walk of the Caminho da Nazaré, Nazaré → Fátima.
Lives at `/hike-nazare/` (`https://mehul.pt/hike-nazare/`).

It is a plain file under `static/`, so Hugo copies it verbatim: no layout wraps it, and
none of `config.toml`, `layouts/` or `assets/sass/` affects it.

## ⚠️ `index.html` is generated — do not hand-edit it

It is written by `build/gen.py` from `build/template.html`. Any manual edit is lost on the
next run. Edit the **template**, then regenerate:

```sh
/usr/bin/python3 static/hike-nazare/build/gen.py   # bare `python3` fails: asdf has no version set
rm -rf public/hike-nazare && hugo                  # the rm matters; see below
```

`hugo` does **not** delete files that disappeared from `static/`, so a rename (like the GPX
one below) leaves the old file in `public/` forever unless that directory is cleared first.

## Inputs

| File | Holds |
| --- | --- |
| `gpx/caminho-da-nazare.gpx` | The route |
| `accomadation.txt` | Stays, one per line, **in trip order** |
| `transportation.txt` | Bus legs, one per line, in trip order |

Both `.txt` formats are documented in a `#` comment header in the file itself; `gen.py`
skips `#` lines. Line order is meaningful — **do not sort them**. In `accomadation.txt` the
first line is the night before setting off and each later line ends a walking day, which is
what makes the day count fall out of the data. Add a third stay line and the page grows a
Day 3 with its own colour, split line and profile segment automatically.

## The GPX has two traps

1. **It is routes, not tracks.** Three `<rte>` elements (`Day 1/2/3`) of `<rtept>`, with no
   `<trk>`, `<trkpt>` or `<time>`. Any library or snippet that reads only tracks renders an
   empty map. Every point has `<ele>`.
2. **`Day 2` and `Day 3` are stored in reverse walking order.** Endpoint distances prove it:
   `Day 1.last → Day 2.last = 0.00 km` (vs 9.05 km to `Day 2.first`), and
   `Day 2.first → Day 3.last = 0.00 km` (vs 12.41 km). `gen.py` detects this rather than
   hardcoding it, chaining each route on by whichever endpoint is nearer the growing tail,
   and drops the duplicated join point. Result: one continuous path, 0 km gaps at both joins.

Reversing a segment swaps its climb and descent, so the corrected direction reports
**+1502 m**, not the 1313 m you get from summing the file as stored.

## Numbers (all derived, none hardcoded)

| | Distance | Climb / descent |
| --- | --- | --- |
| Day 1 — Nazaré → Porto de Mós | 30.5 km | +758 / −732 m |
| Day 2 — Porto de Mós → Fátima | 25.5 km | +744 / −528 m |
| **Total** | **56.0 km** | **+1502 / −1260 m** |

3355 points after merging. Elevation 12.8–459 m.

## The two-day split is not a GPX boundary

The GPX's own three-day staging is the Hiiker app's default and was **discarded**. The walk
is two days, split where the route passes closest to the second stay (Singer's Lounge):
route index **1643**, 30.5 km in, **185 m** off-route. Neither GPX boundary is near that
lodge (they sit 3.9 km and 7.2 km away), so using them would have given a lopsided
24.7 / 31.3 km split. `gen.py` recomputes the index from the coordinates every run.

## No dates anywhere — this is deliberate

Dates were stripped for privacy. That included **renaming the GPX**, which used to be
`2026-09-29 Caminho da Nazaré.gpx` and leaked the export date in a publicly served
filename. The GPX's contents were already clean (no `<time>`).

`gen.py` has a **privacy guard**: before writing it regex-scans the output for
`DD-MM-YYYY`, `YYYY-MM-DD` and `1 Jan 2026` forms and refuses to write if any appear. It
prints `privacy check: no dates in output` on success. Do not reintroduce dates into the
`.txt` files without deciding to remove that guard.

### Consequence: the timeline orders by structure, not time

With no dates, chronology is derived from a `(phase, slot)` sort key —
`phase 0` = the day before, `phase N` = the Nth walking day; slots are
`1` inbound travel, `2` the walk, `3` outbound travel, `4` the night.

| Entry | phase | slot |
| --- | --- | --- |
| Bus whose `to` is the start town | 0 | 1 |
| Stay with `role === 'start'` | 0 | 4 |
| Walking day *i* | i | 2 |
| Nth overnight stay | n | 4 |
| Bus whose `from` is the finish town | N | 3 |

Clock times only break ties within a slot. Current output:
`Bus Porto→Nazaré, Casa da Cristina, Walk 1, Singer's Lounge, Walk 2, Bus Fátima→Porto`,
grouped under `Day before / Day 1 / Day 2`.

## Design decisions worth not undoing

- **Page structure is Itinerary → Route → Elevation**, with the totals as a summary line
  under the subtitle. The map is deliberately *not* first.
- **The timeline is the map key.** Its markers reuse the map's symbols: a coloured bar =
  the polyline for that day, a filled circle = an overnight stop, a hollow square = a bus
  terminal pin. This is why there is no separate legend — don't add one back without
  changing the markers.
- **An overnight is coloured by the day just completed**, in both the timeline and the map,
  so the two agree. Singer's Lounge is therefore Day 1 blue, not Day 2 orange.
- **Far terminals get a marker but are excluded from the initial map bounds.** TIC Campanhã
  (Porto) is 169 km north; framing it would shrink the 56 km walk to a squiggle. Threshold
  is `NEAR_M = 25000` in `gen.py`; the card says "169 km off the map" so the marker isn't a
  mystery.
- **Coordinates are inlined** into `index.html` rather than fetched, so there is no network
  call, no filename escaping and the page works opened as a local file.
- **No blog header or "Written by" footer**, by request — this page is not presented as part
  of the blog. The `<title>` is just "Caminho da Nazaré".
- Styling mirrors the tokens in `assets/sass/_base.scss`: PT Serif, `#fafafa` background,
  `#1d242b` text, `#6f6b6b` muted, `#dfdfdf` rules, `#0077c0` accent, 840 px max-width. Day
  palette is `#0077c0, #b85c00, #2a7d45, #7b2d8b`, taken from the site's tag colours.
- The GPX download link stays `encodeURIComponent`'d even though the filename is now ASCII.

## How to verify changes without a browser

There was no browser extension available in the session that built this, so the page's real
JavaScript was executed headlessly under JavaScriptCore with DOM/Leaflet stubs. `build/stub.js`
is that harness. It is the fastest way to check a change didn't break the wiring:

```sh
cd static/hike-nazare
/usr/bin/python3 -c "import re;h=open('index.html',encoding='utf-8').read();\
open('/tmp/page.js','w',encoding='utf-8').write(re.findall(r'<script>(.*?)</script>',h,re.S)[0])"
cat build/stub.js /tmp/page.js > /tmp/run.js
# append your own print() assertions to /tmp/run.js, then:
/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc /tmp/run.js
```

Things worth asserting, all of which held at the last change: 6 timeline entries in
chronological order across 3 groups; per-day distances summing to 56.0 km; the two
polylines sharing their junction point exactly; 4 profile paths with no `NaN`; 2 stay
markers + 2 terminal pins; map bounds at 3359 points (route + stays + the *near* terminal
only); and a regex sweep finding no dates.

**Not covered by the harness:** actual tile rendering, the visual look, and responsive
behaviour. Those still need a real browser.

## Outstanding / known issues

- **Everything in this folder is published**, because it is under `static/`. That currently
  includes `accomadation.txt`, `transportation.txt`, this `CONTEXT.md` and all of `build/` —
  reachable as e.g. `mehul.pt/hike-nazare/accomadation.txt`. The addresses are on the page
  by choice, but the raw inputs and build tooling probably shouldn't ship. Moving
  `build/` + the two `.txt` files to a sibling `tools/hike-nazare/` and pointing `gen.py`'s
  `SRC` at the page folder would fix it; `gen.py` uses paths relative to its own location,
  so it only needs its two path constants adjusted.
- `static/hike-nazare/.DS_Store` is being published too. `.DS_Store` is **not** in
  `.gitignore`; several exist across the repo.
- Nothing in this folder is committed yet — it is all untracked.
- No coordinates exist for where the Porto → Nazaré bus *arrives* in Nazaré, so only the two
  departure terminals are mapped. Add a Maps link and the format supports it.
- The repo also had 12 deleted post images under `content/posts/` unstaged, unrelated to
  this page.
