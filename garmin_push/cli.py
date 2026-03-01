"""CLI interface for garmin-push.

Usage:
    garmin-push login                                  # Authenticate and save tokens
    garmin-push push workouts/tempo.yaml               # Upload workout from YAML
    garmin-push push workouts/tempo.yaml --schedule 2026-03-15
    garmin-push quick easy 45                          # 45-min easy run
    garmin-push quick intervals 6x400m                 # 6x400m repeats
    garmin-push quick tempo 20                         # 20-min tempo
    garmin-push quick long 90                          # 90-min long run
    garmin-push list                                   # List workouts
"""

import argparse
import re
import sys

import yaml

from . import auth, client, models


def cmd_login(args: argparse.Namespace) -> None:
    """Authenticate with Garmin Connect and save tokens."""
    garmin = auth.get_client(email=args.email)
    name = garmin.display_name or garmin.full_name or "user"
    print(f"Logged in as {name}. Tokens saved to ~/.garmin-push/tokens/")


def cmd_push(args: argparse.Namespace) -> None:
    """Upload workout(s) from YAML file(s)."""
    garmin = auth.get_client()

    for filepath in args.files:
        with open(filepath) as f:
            data = yaml.safe_load(f)

        workouts_data = data.get("workouts", [data])  # support single or list

        for wdata in workouts_data:
            name = wdata["name"]
            steps = wdata["steps"]
            duration = wdata.get("estimated_duration_minutes", 30)

            workout = models.build_workout(name, steps, duration)
            result = client.upload_workout(garmin, workout)
            workout_id = result.get("workoutId", "unknown")
            print(f"Uploaded '{name}' (ID: {workout_id})")

            if args.schedule:
                client.schedule_workout(garmin, workout_id, args.schedule)
                print(f"  Scheduled to {args.schedule}")


def cmd_quick(args: argparse.Namespace) -> None:
    """Create a quick workout without a YAML file."""
    workout_type = args.type
    spec = args.spec

    if workout_type == "easy":
        minutes = int(spec)
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
        minutes = int(spec)
        name = args.name or f"Long Run {minutes}min"
        steps = [
            {"kind": "warmup", "duration": "10:00"},
            {"kind": "run", "duration": f"{minutes - 20}:00", "pace": "easy"},
            {"kind": "cooldown", "duration": "10:00"},
        ]
        duration = minutes

    elif workout_type == "tempo":
        tempo_min = int(spec)
        name = args.name or f"Tempo {tempo_min}min"
        steps = [
            {"kind": "warmup", "duration": "10:00"},
            {"kind": "run", "duration": f"{tempo_min}:00", "pace": "tempo"},
            {"kind": "cooldown", "duration": "10:00"},
        ]
        duration = tempo_min + 20

    elif workout_type == "intervals":
        # Parse spec like "6x400m", "4x1km", "8x200m"
        m = re.match(r"^(\d+)x(.+)$", spec)
        if not m:
            print(f"Invalid interval spec: {spec!r}. Use format like '6x400m'")
            sys.exit(1)
        count = int(m.group(1))
        distance = m.group(2)
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
        duration = 40  # rough estimate

    else:
        print(f"Unknown workout type: {workout_type}")
        sys.exit(1)

    garmin = auth.get_client()
    workout = models.build_workout(name, steps, duration)
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

    # push
    push_p = subparsers.add_parser("push", help="Upload workout(s) from YAML file(s)")
    push_p.add_argument("files", nargs="+", help="YAML workout file(s)")
    push_p.add_argument("--schedule", default=None, help="Schedule to date (YYYY-MM-DD)")

    # quick
    quick_p = subparsers.add_parser("quick", help="Quick workout without YAML")
    quick_p.add_argument(
        "type", choices=["easy", "intervals", "tempo", "long"],
        help="Workout type",
    )
    quick_p.add_argument("spec", help="Duration in min, or NxDIST for intervals")
    quick_p.add_argument("--name", default=None, help="Custom workout name")
    quick_p.add_argument("--schedule", default=None, help="Schedule to date (YYYY-MM-DD)")

    # list
    list_p = subparsers.add_parser("list", help="List workouts on Garmin Connect")
    list_p.add_argument("--limit", type=int, default=20, help="Max workouts to show")

    args = parser.parse_args()

    commands = {
        "login": cmd_login,
        "push": cmd_push,
        "quick": cmd_quick,
        "list": cmd_list,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
