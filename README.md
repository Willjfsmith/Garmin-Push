# Home Strength Blueprint

A mobile-first, offline-capable web app for the **Home Strength Blueprint** — an
11-minute daily strength workout you can run with bodyweight, resistance bands,
or dumbbells. Open it, pick your kit, see today's five moves, tap **Start**, and
a guided timer walks you through it. No accounts, no backend, no build step.

## What's inside

| File | Purpose |
| --- | --- |
| `index.html` | The entire app — all HTML, CSS and JS inline. Works from `file://`. |
| `manifest.webmanifest` | PWA metadata (name, colors, icons). |
| `sw.js` | Cache-first service worker (only registers over HTTPS). |
| `icon-192.png`, `icon-512.png`, `apple-touch-icon.png` | App icons. |

Everything is self-contained — no frameworks, no CDN, no network calls at
runtime. All your data lives in `localStorage` under the single key `hsb.v1`
and never leaves the device.

## The workout

Five movement patterns (Squat, Hinge, Push, Pull, Core), done twice through,
**45 seconds on / 15 seconds off**, with a 60-second breather between the two
rounds. No warm-up phase, no cool-down phase.

| Round 1 | Break | Round 2 | Total |
| --- | --- | --- | --- |
| 5 × 45s work, 15s rest | 60s | 5 × 45s work, 15s rest | **10:30** |

Every working set is AMRAP — as many good reps as you can in the 45 seconds.
Once you clear the kit's rep ceiling, the app tells you to add load next time.

There is no weekly plan and no target. Open the app, pick a kit, train. The
Progress tab keeps your streak and history; nothing tells you which day to do
what.

### Three kits

| BW · Bodyweight | BD · Bands | DB · Dumbbells |
| --- | --- | --- |
| Bodyweight Squat | Banded Squat | Goblet Squat |
| Glute Bridge | Band Good Morning | DB Romanian Deadlift |
| Push-Up | Band Overhead Press | DB Floor Press |
| Towel Door Row | Band Lat Pulldown | Bent-Over DB Row |
| Plank | Pallof Press | Suitcase Carry |

Those are the defaults. Every slot has alternates — tap **⇄** next to a move on
the Today tab to cycle through them. Your picks are remembered per kit.

### Quick Session

One move, straight sets, a rest timer in between. Push-ups by default, or pick
any move from the library.

- **Reps mode** — e.g. 5 sets × 5 reps with 30s rest. Each set counts up until
  you tap **Done**, then the rest timer runs.
- **Timed mode** — e.g. 5 × 45s with 30s rest, counting down like the main
  session.
- Presets (5×5, 3×10, 10×10) or type your own sets / reps / rest.

Quick sessions log like everything else. Three in a day count as a full day for
your streak.

## Usage

### (a) Open it directly — no hosting

1. Download this folder (or just `index.html`).
2. Open `index.html` in your phone's browser.
3. **Add to Home Screen** / bookmark it. It opens straight to today's workout.

Core features (workout player, timers, logging, progression, export/import) all
work offline from the local file — no service worker required.

### (b) Host it for a full installable PWA

Serve the folder over HTTPS — e.g. **GitHub Pages**:

1. Push this folder to a repo.
2. In the repo settings, enable **Pages** from the branch/`root`.
3. Visit the published URL and use your browser's **Install app** option.

When served over HTTPS the service worker registers automatically and precaches
everything, so the app is fully installable and works offline after the first
load.

## Data & backup

Open **Settings → Backup** to copy your data out as JSON or paste a backup back
in. Use it to move your history to another device or keep a safety copy. If the
stored data is ever corrupted, the app backs up the raw string to
`hsb.v1.corrupt` and starts fresh rather than losing the app.

Data from the earlier five-column version migrates automatically: old logs keep
their history, and the old kits map onto Bodyweight, Bands, and Dumbbells.

## Privacy

No accounts, no analytics, no network calls. Your logs stay in your browser.
