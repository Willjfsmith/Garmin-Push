# Home Strength Blueprint

A mobile-first, offline web app for short home strength workouts — dumbbells,
resistance bands, or no equipment. No accounts, no backend, no build step:
one `index.html` with everything inline. Your data lives in your browser's
`localStorage` and never leaves the device.

## How it works

- **Pick your set** — five workout types: A Dumbbells·Heavy, B Bands·Volume,
  C No‑Equipment·Tempo, D No‑Equipment·Power, E Full Kit·Mix. Each is five
  moves (Squat / Hinge / Push / Pull / Core).
- **Customise the moves** — tap **Swap** on any move to pick from that
  pattern's whole library (this set's variants plus every other set's), or
  leave a move out entirely.
- **Set the timing before you start** — Work / Rest / Rounds steppers and
  one-tap presets (45/15, 40/20, …) sit right above Start, plus warm-up and
  cool-down toggles. The Start button shows the real session length.
- **AMRAP intervals** — no prescribed reps, and fully hands-free: every work
  interval and rest advances on its own (3-2-1 ticks, then a cue). Tap
  "Done early" if you want to move on sooner. Do as many good reps as you
  can; the app tells you the number to beat, and when you clear the ceiling
  it tells you to add load.
- **Log as you go** — during each rest (and the cool-down) a one-tap rep pad
  logs the set you just finished, weight prefilled. The end screen is just a
  recap + save.
- **Snacks** — self-set daily mini-goals ("10 push-ups, 4× today"). Tap the
  card each time you do a set; hit all your goals and the day counts toward
  your streak.
- **Quick Log (＋)** — did a few reps out of nowhere? Log any move in two taps.
- **Progress** — weekly stats, 8-week heatmap, personal records (est. 1RM for
  weighted moves, rep bests for bodyweight), bodyweight tracking, badges.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | The entire app — HTML, CSS and JS inline. |
| `manifest.webmanifest`, `sw.js` | PWA install + offline cache (HTTPS only). |
| `icon-192.png`, `icon-512.png`, `apple-touch-icon.png` | App icons. |

## Using it on a phone (recommended: iPhone + hosted)

Host the folder on any static host (Vercel, GitHub Pages, Netlify — a Vercel
deploy of this repo works as-is):

1. Open the URL in Safari.
2. Share → **Add to Home Screen**.
3. Launch from the icon: full-screen, offline after first load, and the
   home-screen app's storage is exempt from Safari's 7-day data eviction.

Opening `index.html` directly from disk also works (desktop/Android) — core
features don't need the service worker.

## Backing up

Settings → Backup: **Download file** saves a `.json` of everything (stash it
in iCloud Drive/Files occasionally), and Import restores it. Data is
device-local — there is no sync between devices by design.
