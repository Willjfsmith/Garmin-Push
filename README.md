# Home Strength Blueprint

A mobile-first, offline-capable web app for the **Home Strength Blueprint** — a
15-minute daily strength program you can run with dumbbells, resistance bands,
or no equipment at all. Open it, see today's five exercises, tap **Start**, and
a guided session with timers walks you through it. No accounts, no backend, no
build step.

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

## The program

Five movement patterns (Squat, Hinge, Push, Pull, Core) across five equipment
tiers (columns **A–E**). Each weekday maps to a column:

| Mon | Tue | Wed | Thu | Fri | Sat / Sun |
| --- | --- | --- | --- | --- | --- |
| A · Dumbbells (Heavy) | B · Bands (Volume) | C · No Equipment (Tempo) | D · No Equipment (Power) | E · Full Kit (Mix) | Rest / repeat a favorite |

Progress runs on a repeating **4-week cycle** (Baseline → +1 Rep → Top of Range
→ Add Weight) using double progression: the app looks at your last log for each
exercise and tells you what to aim for today.

### Two ways to train
- **15-minute session** — warm-up → two rounds of the five exercises with rest
  timers → cool-down → quick-log your sets.
- **Snack Mode** — the same five moves spread across the day as five 3-minute
  micro-sessions, ticked off one at a time. All five = a complete day.

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

## Privacy

No accounts, no analytics, no network calls. Your logs stay in your browser.
