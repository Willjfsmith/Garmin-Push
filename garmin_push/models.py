"""Workout definition models and Garmin JSON builder.

Handles parsing user-friendly workout definitions (from YAML or CLI)
and converting them to Garmin Connect workout JSON via the garminconnect library.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from garminconnect.workout import (
    ConditionType,
    ExecutableStep,
    RepeatGroup,
    RunningWorkout,
    SportType,
    StepType,
    TargetType,
    WorkoutSegment,
)


# --- Pace / duration parsing utilities ---


def parse_pace(pace_str: str) -> float:
    """Convert pace string like '5:30' (min:sec per km) to meters/second.

    5:30 = 330 seconds per km = 1000/330 ≈ 3.03 m/s
    """
    pace_str = pace_str.strip()
    parts = pace_str.split(":")
    if len(parts) not in (1, 2):
        raise ValueError(f"Invalid pace format: {pace_str!r}. Use 'M:SS' (e.g. '5:30')")
    try:
        minutes = int(parts[0])
        seconds = int(parts[1]) if len(parts) > 1 else 0
    except ValueError:
        raise ValueError(f"Invalid pace format: {pace_str!r}. Use 'M:SS' (e.g. '5:30')")
    if minutes < 0 or seconds < 0 or seconds >= 60:
        raise ValueError(f"Invalid pace: {pace_str!r}. Seconds must be 0-59")
    total_seconds = minutes * 60 + seconds
    if total_seconds <= 0:
        raise ValueError(f"Pace must be greater than 0:00")
    return 1000.0 / total_seconds


def parse_time(time_str: str) -> float:
    """Parse time string to seconds. Supports 'Xmin', 'MM:SS', 'HH:MM:SS'."""
    time_str = time_str.strip()

    # Handle "45min", "10min" format
    m = re.match(r"^(\d+)\s*min$", time_str)
    if m:
        return int(m.group(1)) * 60.0

    # Handle "30sec", "90sec" format
    m = re.match(r"^(\d+)\s*sec$", time_str)
    if m:
        return float(m.group(1))

    # Handle MM:SS or HH:MM:SS
    parts = time_str.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

    raise ValueError(f"Cannot parse time: {time_str!r}")


def parse_distance(dist_str: str) -> float:
    """Parse distance string to meters. Supports '400m', '1.5km', '1mi'."""
    dist_str = dist_str.strip().lower()

    m = re.match(r"^([\d.]+)\s*km$", dist_str)
    if m:
        return float(m.group(1)) * 1000.0

    m = re.match(r"^([\d.]+)\s*mi$", dist_str)
    if m:
        return float(m.group(1)) * 1609.34

    m = re.match(r"^([\d.]+)\s*m$", dist_str)
    if m:
        return float(m.group(1))

    raise ValueError(f"Cannot parse distance: {dist_str!r}")


# --- Default pace zones (min/km) ---

DEFAULT_PACE_ZONES: dict[str, tuple[str, str]] = {
    "easy": ("6:00", "6:30"),
    "moderate": ("5:20", "5:40"),
    "tempo": ("4:40", "5:00"),
    "threshold": ("4:20", "4:40"),
    "interval": ("3:50", "4:10"),
    "sprint": ("3:20", "3:40"),
}


def resolve_pace(pace_value: Any, pace_zones: dict | None = None) -> tuple[float, float] | None:
    """Resolve a pace value to (slow_mps, fast_mps) tuple.

    pace_value can be:
      - None -> no target
      - A zone name string like "easy" or "tempo"
      - A range string like "5:00-5:30"
      - A list/tuple of two pace strings ["5:00", "5:30"]
    """
    if pace_value is None:
        return None

    zones = pace_zones or DEFAULT_PACE_ZONES

    if isinstance(pace_value, str):
        if pace_value in zones:
            pace_a, pace_b = zones[pace_value]
        elif "-" in pace_value:
            pace_a, pace_b = pace_value.split("-", 1)
        else:
            raise ValueError(
                f"Unknown pace zone: {pace_value!r}. "
                f"Available zones: {', '.join(zones.keys())}"
            )
    elif isinstance(pace_value, (list, tuple)) and len(pace_value) == 2:
        pace_a, pace_b = pace_value[0], pace_value[1]
    else:
        raise ValueError(f"Invalid pace value: {pace_value!r}")

    mps_a = parse_pace(pace_a)
    mps_b = parse_pace(pace_b)
    # Garmin expects targetValueOne < targetValueTwo (slower pace = lower m/s first)
    slow_mps = min(mps_a, mps_b)
    fast_mps = max(mps_a, mps_b)
    return (slow_mps, fast_mps)


# --- Garmin workout JSON building ---

SPORT_TYPE_RUNNING = {
    "sportTypeId": SportType.RUNNING,
    "sportTypeKey": "running",
    "displayOrder": 1,
}

NO_TARGET = {
    "workoutTargetTypeId": TargetType.NO_TARGET,
    "workoutTargetTypeKey": "no.target",
    "displayOrder": 1,
}


def _make_pace_target() -> dict:
    """Return the targetType dict for a pace-based target."""
    return {
        "workoutTargetTypeId": TargetType.SPEED,
        "workoutTargetTypeKey": "pace.zone",
        "displayOrder": 1,
    }


def _make_end_condition_time(seconds: float) -> tuple[dict, float]:
    return (
        {
            "conditionTypeId": ConditionType.TIME,
            "conditionTypeKey": "time",
            "displayOrder": 2,
            "displayable": True,
        },
        seconds,
    )


def _make_end_condition_distance(meters: float) -> tuple[dict, float]:
    return (
        {
            "conditionTypeId": ConditionType.DISTANCE,
            "conditionTypeKey": "distance",
            "displayOrder": 1,
            "displayable": True,
        },
        meters,
    )


def _make_end_condition_lap_button() -> tuple[dict, None]:
    return (
        {
            "conditionTypeId": 1,
            "conditionTypeKey": "lap.button",
            "displayOrder": 1,
            "displayable": False,
        },
        None,
    )


# Step type name -> Garmin step type dict
_STEP_TYPES = {
    "warmup": {"stepTypeId": StepType.WARMUP, "stepTypeKey": "warmup", "displayOrder": 1},
    "cooldown": {"stepTypeId": StepType.COOLDOWN, "stepTypeKey": "cooldown", "displayOrder": 2},
    "run": {"stepTypeId": StepType.INTERVAL, "stepTypeKey": "interval", "displayOrder": 3},
    "interval": {"stepTypeId": StepType.INTERVAL, "stepTypeKey": "interval", "displayOrder": 3},
    "recover": {"stepTypeId": StepType.RECOVERY, "stepTypeKey": "recovery", "displayOrder": 4},
    "recovery": {"stepTypeId": StepType.RECOVERY, "stepTypeKey": "recovery", "displayOrder": 4},
    "rest": {"stepTypeId": StepType.REST, "stepTypeKey": "rest", "displayOrder": 5},
}


def _build_step(
    step_def: dict, order: int, pace_zones: dict | None = None
) -> ExecutableStep:
    """Build a single ExecutableStep from a step definition dict.

    step_def keys:
      - kind: warmup|cooldown|run|interval|recover|recovery|rest
      - duration: "10:00" or "400m" or "lap"
      - pace: optional - zone name, range string, or [slow, fast] list
    """
    kind = step_def["kind"]
    step_type = _STEP_TYPES[kind]

    # Parse duration / end condition
    duration = step_def.get("duration", "lap")
    if duration == "lap":
        end_cond, end_val = _make_end_condition_lap_button()
    else:
        # Auto-detect distance vs time
        duration_type = step_def.get("duration_type")
        if duration_type == "distance" or re.match(r"^[\d.]+\s*(m|km|mi)$", duration):
            meters = parse_distance(duration)
            end_cond, end_val = _make_end_condition_distance(meters)
        else:
            seconds = parse_time(duration)
            end_cond, end_val = _make_end_condition_time(seconds)

    # Parse pace target
    pace_mps = resolve_pace(step_def.get("pace"), pace_zones)

    kwargs: dict[str, Any] = {
        "stepOrder": order,
        "stepType": step_type,
        "endCondition": end_cond,
        "endConditionValue": end_val,
    }

    if pace_mps:
        kwargs["targetType"] = _make_pace_target()
        kwargs["targetValueOne"] = pace_mps[0]
        kwargs["targetValueTwo"] = pace_mps[1]
    else:
        kwargs["targetType"] = NO_TARGET

    return ExecutableStep(**kwargs)


def _build_repeat(
    repeat_def: dict, order: int, pace_zones: dict | None = None
) -> RepeatGroup:
    """Build a RepeatGroup from a repeat definition dict.

    repeat_def keys:
      - repeat: number of iterations
      - steps: list of step definition dicts
    """
    iterations = repeat_def["repeat"]
    inner_steps = []
    for i, step_def in enumerate(repeat_def["steps"]):
        inner_steps.append(_build_step(step_def, order=i + 1, pace_zones=pace_zones))

    return RepeatGroup(
        stepOrder=order,
        stepType={"stepTypeId": StepType.REPEAT, "stepTypeKey": "repeat", "displayOrder": 6},
        numberOfIterations=iterations,
        workoutSteps=inner_steps,
        endCondition={
            "conditionTypeId": ConditionType.ITERATIONS,
            "conditionTypeKey": "iterations",
            "displayOrder": 7,
            "displayable": False,
        },
        endConditionValue=float(iterations),
    )


def build_workout(
    name: str,
    steps: list[dict],
    estimated_duration_minutes: int = 30,
    pace_zones: dict | None = None,
) -> RunningWorkout:
    """Build a RunningWorkout from a list of step/repeat definitions.

    Args:
        name: Workout name as it will appear in Garmin Connect.
        steps: List of step dicts. Each has 'kind'+'duration' for a step,
               or 'repeat'+'steps' for a repeat group.
        estimated_duration_minutes: Estimated total duration.
        pace_zones: Optional custom pace zones dict.

    Returns:
        RunningWorkout ready for upload via garminconnect.
    """
    all_steps: list[ExecutableStep | RepeatGroup] = []
    order = 1
    for item in steps:
        if "repeat" in item:
            all_steps.append(_build_repeat(item, order, pace_zones))
        else:
            all_steps.append(_build_step(item, order, pace_zones))
        order += 1

    segment = WorkoutSegment(
        segmentOrder=1,
        sportType=SPORT_TYPE_RUNNING,
        workoutSteps=all_steps,
    )

    return RunningWorkout(
        workoutName=name,
        estimatedDurationInSecs=estimated_duration_minutes * 60,
        workoutSegments=[segment],
    )


def _format_seconds(s: float) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    s = int(s)
    if s >= 3600:
        return f"{s // 3600}:{(s % 3600) // 60:02d}:{s % 60:02d}"
    return f"{s // 60}:{s % 60:02d}"


def _format_meters(m: float) -> str:
    """Format meters as human-readable distance."""
    if m >= 1000:
        return f"{m / 1000:.1f}km"
    return f"{int(m)}m"


def _mps_to_pace(mps: float) -> str:
    """Convert m/s to min:sec per km pace string."""
    secs_per_km = 1000.0 / mps
    mins = int(secs_per_km) // 60
    secs = int(secs_per_km) % 60
    return f"{mins}:{secs:02d}"


def format_workout_summary(workout: RunningWorkout) -> str:
    """Return a human-readable summary of a workout for dry-run output."""
    d = workout.to_dict()
    lines = [f"Workout: {d['workoutName']}"]
    lines.append(f"Duration: ~{_format_seconds(d['estimatedDurationInSecs'])}")
    lines.append("Steps:")

    for step in d["workoutSegments"][0]["workoutSteps"]:
        step_type = step.get("stepType", {}).get("stepTypeKey", "?")

        if step_type == "repeat":
            n = step.get("numberOfIterations", "?")
            lines.append(f"  Repeat x{n}:")
            for inner in step.get("workoutSteps", []):
                lines.append(f"    {_format_step_line(inner)}")
        else:
            lines.append(f"  {_format_step_line(step)}")

    return "\n".join(lines)


def _format_step_line(step: dict) -> str:
    """Format a single step dict as a summary line."""
    kind = step.get("stepType", {}).get("stepTypeKey", "?")
    cond_key = step.get("endCondition", {}).get("conditionTypeKey", "?")
    cond_val = step.get("endConditionValue")

    if cond_key == "time" and cond_val:
        duration_str = _format_seconds(cond_val)
    elif cond_key == "distance" and cond_val:
        duration_str = _format_meters(cond_val)
    elif cond_key == "lap.button":
        duration_str = "lap button"
    else:
        duration_str = "?"

    target_key = step.get("targetType", {}).get("workoutTargetTypeKey", "no.target")
    if target_key == "pace.zone":
        tv1 = step.get("targetValueOne", 0)
        tv2 = step.get("targetValueTwo", 0)
        pace_str = f" @ {_mps_to_pace(tv2)}-{_mps_to_pace(tv1)}/km"
    else:
        pace_str = ""

    return f"{kind} {duration_str}{pace_str}"
