"""Tests for garmin_push.models - parsing, validation, and workout building."""

import pytest

from garmin_push.models import (
    DEFAULT_PACE_ZONES,
    build_workout,
    format_workout_summary,
    parse_distance,
    parse_pace,
    parse_time,
    resolve_pace,
)


# --- parse_pace ---


class TestParsePace:
    def test_five_thirty(self):
        # 5:30 = 330s/km = 1000/330 ≈ 3.03 m/s
        assert abs(parse_pace("5:30") - 1000.0 / 330) < 0.001

    def test_four_zero(self):
        # 4:00 = 240s/km = 1000/240 ≈ 4.167 m/s
        assert abs(parse_pace("4:00") - 1000.0 / 240) < 0.001

    def test_six_zero(self):
        assert abs(parse_pace("6:00") - 1000.0 / 360) < 0.001

    def test_strips_whitespace(self):
        assert parse_pace("  5:30  ") == parse_pace("5:30")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid pace format"):
            parse_pace("abc")

    def test_invalid_colon_format_raises(self):
        with pytest.raises(ValueError, match="Invalid pace format"):
            parse_pace("5:ab")

    def test_seconds_over_59_raises(self):
        with pytest.raises(ValueError, match="Seconds must be 0-59"):
            parse_pace("5:60")

    def test_zero_pace_raises(self):
        with pytest.raises(ValueError, match="greater than 0:00"):
            parse_pace("0:00")

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            parse_pace("-1:00")


# --- parse_time ---


class TestParseTime:
    def test_mm_ss(self):
        assert parse_time("10:00") == 600.0

    def test_mm_ss_nonzero_seconds(self):
        assert parse_time("5:30") == 330.0

    def test_hh_mm_ss(self):
        assert parse_time("1:30:00") == 5400.0

    def test_minutes_format(self):
        assert parse_time("45min") == 2700.0

    def test_seconds_format(self):
        assert parse_time("90sec") == 90.0

    def test_strips_whitespace(self):
        assert parse_time("  10:00  ") == 600.0

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Cannot parse time"):
            parse_time("abc")


# --- parse_distance ---


class TestParseDistance:
    def test_meters(self):
        assert parse_distance("400m") == 400.0

    def test_kilometers(self):
        assert parse_distance("1km") == 1000.0

    def test_fractional_km(self):
        assert parse_distance("1.5km") == 1500.0

    def test_miles(self):
        assert abs(parse_distance("1mi") - 1609.34) < 0.01

    def test_case_insensitive(self):
        assert parse_distance("1KM") == 1000.0

    def test_strips_whitespace(self):
        assert parse_distance("  400m  ") == 400.0

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Cannot parse distance"):
            parse_distance("abc")


# --- resolve_pace ---


class TestResolvePace:
    def test_none_returns_none(self):
        assert resolve_pace(None) is None

    def test_zone_name(self):
        slow, fast = resolve_pace("easy")
        # easy = ("6:00", "6:30") -> slow ≈ 2.56 m/s, fast ≈ 2.78 m/s
        assert slow < fast
        assert abs(slow - parse_pace("6:30")) < 0.001
        assert abs(fast - parse_pace("6:00")) < 0.001

    def test_range_string(self):
        slow, fast = resolve_pace("5:00-5:30")
        assert slow < fast

    def test_list_pair(self):
        slow, fast = resolve_pace(["5:00", "5:30"])
        assert slow < fast

    def test_reversed_range_sorted(self):
        # Even if given backwards, should return (slow, fast)
        slow, fast = resolve_pace("5:30-5:00")
        assert slow < fast

    def test_unknown_zone_raises(self):
        with pytest.raises(ValueError, match="Unknown pace zone"):
            resolve_pace("nonexistent")

    def test_unknown_zone_shows_available(self):
        with pytest.raises(ValueError, match="Available zones"):
            resolve_pace("nonexistent")

    def test_custom_zones(self):
        custom = {"jog": ("7:00", "7:30")}
        slow, fast = resolve_pace("jog", custom)
        assert slow < fast

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="Invalid pace value"):
            resolve_pace(12345)


# --- build_workout ---


class TestBuildWorkout:
    def test_simple_easy_run(self):
        steps = [
            {"kind": "warmup", "duration": "10:00"},
            {"kind": "run", "duration": "30:00", "pace": "easy"},
            {"kind": "cooldown", "duration": "5:00"},
        ]
        workout = build_workout("Easy Run", steps, 45)
        d = workout.to_dict()
        assert d["workoutName"] == "Easy Run"
        assert d["estimatedDurationInSecs"] == 2700
        assert len(d["workoutSegments"][0]["workoutSteps"]) == 3

    def test_interval_workout_with_repeats(self):
        steps = [
            {"kind": "warmup", "duration": "10:00"},
            {
                "repeat": 6,
                "steps": [
                    {"kind": "run", "duration": "400m", "duration_type": "distance", "pace": "interval"},
                    {"kind": "recover", "duration": "400m", "duration_type": "distance"},
                ],
            },
            {"kind": "cooldown", "duration": "10:00"},
        ]
        workout = build_workout("6x400m", steps, 40)
        d = workout.to_dict()
        outer_steps = d["workoutSegments"][0]["workoutSteps"]
        assert len(outer_steps) == 3
        repeat = outer_steps[1]
        assert repeat["stepType"]["stepTypeKey"] == "repeat"
        assert repeat["numberOfIterations"] == 6
        assert len(repeat["workoutSteps"]) == 2

    def test_pace_target_values_present(self):
        steps = [{"kind": "run", "duration": "20:00", "pace": "tempo"}]
        workout = build_workout("Tempo", steps, 20)
        d = workout.to_dict()
        step = d["workoutSegments"][0]["workoutSteps"][0]
        assert step["targetType"]["workoutTargetTypeKey"] == "pace.zone"
        assert "targetValueOne" in step
        assert "targetValueTwo" in step
        assert step["targetValueOne"] < step["targetValueTwo"]

    def test_no_pace_target(self):
        steps = [{"kind": "warmup", "duration": "10:00"}]
        workout = build_workout("Warmup", steps, 10)
        d = workout.to_dict()
        step = d["workoutSegments"][0]["workoutSteps"][0]
        assert step["targetType"]["workoutTargetTypeKey"] == "no.target"

    def test_distance_end_condition(self):
        steps = [{"kind": "run", "duration": "1km", "duration_type": "distance"}]
        workout = build_workout("1k", steps, 5)
        d = workout.to_dict()
        step = d["workoutSegments"][0]["workoutSteps"][0]
        assert step["endCondition"]["conditionTypeKey"] == "distance"
        assert step["endConditionValue"] == 1000.0

    def test_lap_button_duration(self):
        steps = [{"kind": "warmup", "duration": "lap"}]
        workout = build_workout("Open Warmup", steps, 10)
        d = workout.to_dict()
        step = d["workoutSegments"][0]["workoutSteps"][0]
        assert step["endCondition"]["conditionTypeKey"] == "lap.button"

    def test_invalid_step_kind_raises(self):
        steps = [{"kind": "invalid", "duration": "10:00"}]
        with pytest.raises(KeyError):
            build_workout("Bad", steps, 10)

    def test_custom_pace_zones(self):
        zones = {"jog": ("7:00", "7:30")}
        steps = [{"kind": "run", "duration": "30:00", "pace": "jog"}]
        workout = build_workout("Jog", steps, 30, pace_zones=zones)
        d = workout.to_dict()
        step = d["workoutSegments"][0]["workoutSteps"][0]
        assert step["targetType"]["workoutTargetTypeKey"] == "pace.zone"


# --- format_workout_summary ---


class TestFormatWorkoutSummary:
    def test_simple_workout_summary(self):
        steps = [
            {"kind": "warmup", "duration": "10:00"},
            {"kind": "run", "duration": "20:00", "pace": "tempo"},
            {"kind": "cooldown", "duration": "10:00"},
        ]
        workout = build_workout("Tempo Run", steps, 40)
        summary = format_workout_summary(workout)
        assert "Tempo Run" in summary
        assert "warmup" in summary
        assert "interval" in summary  # 'run' kind maps to 'interval' step type
        assert "cooldown" in summary
        assert "/km" in summary  # pace target present

    def test_repeat_workout_summary(self):
        steps = [
            {"kind": "warmup", "duration": "10:00"},
            {"repeat": 4, "steps": [
                {"kind": "run", "duration": "400m", "duration_type": "distance", "pace": "interval"},
                {"kind": "recover", "duration": "2:00"},
            ]},
            {"kind": "cooldown", "duration": "10:00"},
        ]
        workout = build_workout("Intervals", steps, 35)
        summary = format_workout_summary(workout)
        assert "Repeat x4" in summary
        assert "400m" in summary
