"""CLI interface for garmin-push.

Usage:
    garmin-push login                                  # Authenticate and save tokens
    garmin-push init                                   # Create starter config file
    garmin-push push workouts/tempo.yaml               # Upload workout from YAML
    garmin-push push workouts/tempo.yaml --schedule 2026-03-15
    garmin-push push workouts/tempo.yaml --dry-run     # Validate without uploading
    garmin-push quick easy 45                          # 45-min easy run
    garmin-push quick intervals 6x400m                 # 6x400m repeats
    garmin-push quick tempo 20                         # 20-min tempo
    garmin-push quick long 90                          # 90-min long run
    garmin-push list                                   # List workouts
"""

import argparse
import datetime
import re
import sys

import yaml
from garminconnect import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

from . import auth, client, models
from .config import create_config, load_config


def _error(msg: str) -> None:
    """Print error message and exit."""
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def _validate_schedule_date(date_str: str | None) -> None:
    """Validate that a schedule date is in YYYY-MM-DD format."""
    if date_str is None:
        return
    try:
        datetime.date.fromisoformat(date_str)
    except ValueError:
        _error(f"Invalid date: {date_str!r}. Use YYYY-MM-DD format (e.g. 2026-03-15)")


def cmd_login(args: argparse.Namespace) -> None:
    """Authenticate with Garmin Connect and save tokens."""
    garmin = auth.get_client(email=args.email)
    name = garmin.display_name or garmin.full_name or "user"
    print(f"Logged in as {name}. Tokens saved to ~/.garmin-push/tokens/")


def cmd_init(args: argparse.Namespace) -> None:
    """Create a starter config file."""
    path = create_config()
    print(f"Config created at {path}")
    print("Edit pace zones to match your fitness level.")


def cmd_push(args: argparse.Namespace) -> None:
    """Upload workout(s) from YAML file(s)."""
    _validate_schedule_date(args.schedule)
    pace_zones = load_config()

    for filepath in args.files:
        try:
            with open(filepath) as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            _error(f"File not found: {filepath}")
        except yaml.YAMLError as e:
            _error(f"Invalid YAML in {filepath}: {e}")

        if not isinstance(data, dict):
            _error(f"Expected a YAML mapping in {filepath}, got {type(data).__name__}")

        workouts_data = data.get("workouts", [data])

        for wdata in workouts_data:
            if "name" not in wdata:
                _error(f"Workout missing 'name' field in {filepath}")
            if "steps" not in wdata:
                _error(f"Workout '{wdata['name']}' missing 'steps' in {filepath}")

            name = wdata["name"]
            steps = wdata["steps"]
            duration = wdata.get("estimated_duration_minutes", 30)

            try:
                workout = models.build_workout(name, steps, duration, pace_zones)
            except (ValueError, KeyError) as e:
                _error(f"Invalid workout '{name}' in {filepath}: {e}")

            if args.dry_run:
                print(models.format_workout_summary(workout))
                print()
                continue

            garmin = auth.get_client()
            result = client.upload_workout(garmin, workout)
            workout_id = result.get("workoutId", "unknown")
            print(f"Uploaded '{name}' (ID: {workout_id})")

            if args.schedule:
                client.schedule_workout(garmin, workout_id, args.schedule)
                print(f"  Scheduled to {args.schedule}")


def cmd_quick(args: argparse.Namespace) -> None:
    """Create a quick workout without a YAML file."""
    _validate_schedule_date(args.schedule)
    pace_zones = load_config()
    workout_type = args.type
    spec = args.spec

    if workout_type == "easy":
        try:
            minutes = int(spec)
        except ValueError:
            _error(f"Expected a number of minutes, got {spec!r}")
        if minutes < 15:
            _error(f"Easy run must be at least 15 minutes (got {minutes})")
        warmup = max(10, minutes // 5)
        cooldown = max(5, minutes // 6)
        main_time = minutes - warmup - cooldown
        name = args.name or f"Easy Run {minutes}min"
        steps = [
            {"kind": "warmup", "duration": f"{warmup}:00"},
            {"kind": "run", "duration": f"{main_time}:00", "pace": "easy"},
            {"kind": "cooldown", "duration": f"{cooldown}:00"},
        ]
        duration = minutes

    elif workout_type == "long":
        try:
            minutes = int(spec)
        except ValueError:
            _error(f"Expected a number of minutes, got {spec!r}")
        if minutes < 30:
            _error(f"Long run must be at least 30 minutes (got {minutes})")
        name = args.name or f"Long Run {minutes}min"
        steps = [
            {"kind": "warmup", "duration": "10:00"},
            {"kind": "run", "duration": f"{minutes - 20}:00", "pace": "easy"},
            {"kind": "cooldown", "duration": "10:00"},
        ]
        duration = minutes

    elif workout_type == "tempo":
        try:
            tempo_min = int(spec)
        except ValueError:
            _error(f"Expected a number of minutes, got {spec!r}")
        if tempo_min < 5:
            _error(f"Tempo block must be at least 5 minutes (got {tempo_min})")
        name = args.name or f"Tempo {tempo_min}min"
        steps = [
            {"kind": "warmup", "duration": "10:00"},
            {"kind": "run", "duration": f"{tempo_min}:00", "pace": "tempo"},
            {"kind": "cooldown", "duration": "10:00"},
        ]
        duration = tempo_min + 20

    elif workout_type == "intervals":
        m = re.match(r"^(\d+)x(.+)$", spec)
        if not m:
            _error(f"Invalid interval spec: {spec!r}. Use format like '6x400m' or '4x1km'")
        count = int(m.group(1))
        distance = m.group(2)
        try:
            models.parse_distance(distance)
        except ValueError:
            _error(f"Invalid distance in interval spec: {distance!r}. Use '400m', '1km', etc.")
        name = args.name or f"{count}x{distance} Intervals"
        steps = [
            {"kind": "warmup", "duration": "10:00"},
            {
                "repeat": count,
                "steps": [
                    {"kind": "run", "duration": distance, "duration_type": "distance", "pace": "interval"},
                    {"kind": "recover", "duration": distance, "duration_type": "distance"},
                ],
            },
            {"kind": "cooldown", "duration": "10:00"},
        ]
        duration = 40

    else:
        _error(f"Unknown workout type: {workout_type}")

    try:
        workout = models.build_workout(name, steps, duration, pace_zones)
    except (ValueError, KeyError) as e:
        _error(f"Failed to build workout: {e}")

    if args.dry_run:
        print(models.format_workout_summary(workout))
        return

    garmin = auth.get_client()
    result = client.upload_workout(garmin, workout)
    workout_id = result.get("workoutId", "unknown")
    print(f"Uploaded '{name}' (ID: {workout_id})")

    if args.schedule:
        client.schedule_workout(garmin, workout_id, args.schedule)
        print(f"  Scheduled to {args.schedule}")


def cmd_list(args: argparse.Namespace) -> None:
    """List workouts on Garmin Connect."""
    garmin = auth.get_client()
    workouts = client.list_workouts(garmin, limit=args.limit)

    if not workouts:
        print("No workouts found.")
        return

    for w in workouts:
        wid = w.get("workoutId", "?")
        name = w.get("workoutName", "Untitled")
        print(f"  {wid}: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="garmin-push",
        description="Push running workouts to Garmin Connect",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # login
    login_p = subparsers.add_parser("login", help="Authenticate with Garmin Connect")
    login_p.add_argument("--email", default=None, help="Garmin Connect email")

    # init
    subparsers.add_parser("init", help="Create starter config file with pace zones")

    # push
    push_p = subparsers.add_parser("push", help="Upload workout(s) from YAML file(s)")
    push_p.add_argument("files", nargs="+", help="YAML workout file(s)")
    push_p.add_argument("--schedule", default=None, help="Schedule to date (YYYY-MM-DD)")
    push_p.add_argument("--dry-run", action="store_true", help="Validate and preview without uploading")

    # quick
    quick_p = subparsers.add_parser("quick", help="Quick workout without YAML")
    quick_p.add_argument(
        "type", choices=["easy", "intervals", "tempo", "long"],
        help="Workout type",
    )
    quick_p.add_argument("spec", help="Duration in min, or NxDIST for intervals")
    quick_p.add_argument("--name", default=None, help="Custom workout name")
    quick_p.add_argument("--schedule", default=None, help="Schedule to date (YYYY-MM-DD)")
    quick_p.add_argument("--dry-run", action="store_true", help="Validate and preview without uploading")

    # list
    list_p = subparsers.add_parser("list", help="List workouts on Garmin Connect")
    list_p.add_argument("--limit", type=int, default=20, help="Max workouts to show")

    args = parser.parse_args()

    commands = {
        "login": cmd_login,
        "init": cmd_init,
        "push": cmd_push,
        "quick": cmd_quick,
        "list": cmd_list,
    }

    try:
        commands[args.command](args)
    except GarminConnectAuthenticationError:
        _error("Authentication failed. Run 'garmin-push login' to re-authenticate.")
    except GarminConnectTooManyRequestsError:
        _error("Rate limited by Garmin. Wait a few minutes and try again.")
    except GarminConnectConnectionError:
        _error("Cannot connect to Garmin. Check your internet connection.")


if __name__ == "__main__":
    main()
