# garmin-push

Push running workouts to Garmin Connect from the command line. Define workouts in YAML or create them quickly via CLI, then upload them to your Garmin account where they sync to your watch.

## Install

```bash
pip install -e .
```

## Setup

### Authenticate

```bash
garmin-push login
```

Enter your Garmin Connect email and password when prompted. Tokens are saved to `~/.garmin-push/tokens/` and are valid for about one year.

You can also set environment variables:

```bash
export GARMIN_EMAIL="your@email.com"
export GARMIN_PASSWORD="yourpassword"
```

## Usage

### Quick workouts

Create common workout types with a single command:

```bash
garmin-push quick easy 45              # 45-minute easy run
garmin-push quick intervals 6x400m    # 6x400m repeats
garmin-push quick tempo 20             # 20-minute tempo block
garmin-push quick long 90              # 90-minute long run
```

Schedule to a specific date:

```bash
garmin-push quick tempo 20 --schedule 2026-03-15
```

### From YAML files

```bash
garmin-push push workouts/examples.yaml
garmin-push push workouts/examples.yaml --schedule 2026-03-20
```

### List uploaded workouts

```bash
garmin-push list
garmin-push list --limit 50
```

## YAML Workout Format

```yaml
workouts:
  - name: "6x400m Intervals"
    estimated_duration_minutes: 40
    steps:
      - kind: warmup
        duration: "10:00"
      - repeat: 6
        steps:
          - kind: run
            duration: 400m
            duration_type: distance
            pace: interval
          - kind: recover
            duration: 400m
            duration_type: distance
      - kind: cooldown
        duration: "10:00"
```

### Step kinds

| Kind | Description |
|------|-------------|
| `warmup` | Warmup period |
| `cooldown` | Cooldown period |
| `run` / `interval` | Main running step |
| `recover` / `recovery` | Recovery between intervals |
| `rest` | Full rest |

### Duration formats

- Time: `"10:00"` (MM:SS), `"1:30:00"` (HH:MM:SS), `"45min"`, `"30sec"`
- Distance: `400m`, `1km`, `1.5mi`
- Open: `"lap"` (press lap button to advance)

### Pace targets

Use built-in zone names or explicit ranges:

| Zone | Default pace (min/km) |
|------|----------------------|
| `easy` | 6:00 - 6:30 |
| `moderate` | 5:20 - 5:40 |
| `tempo` | 4:40 - 5:00 |
| `threshold` | 4:20 - 4:40 |
| `interval` | 3:50 - 4:10 |
| `sprint` | 3:20 - 3:40 |

Or use an explicit range: `pace: "4:00-4:30"`

## How it works

This tool uses the [garminconnect](https://github.com/cyberjunky/python-garminconnect) Python library to authenticate with Garmin Connect and upload structured workouts. Uploaded workouts appear in your Garmin Connect workout library and can be sent to your watch.
