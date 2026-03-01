"""Garmin Connect API operations for workouts."""

from garminconnect import Garmin
from garminconnect.workout import RunningWorkout


def upload_workout(garmin: Garmin, workout: RunningWorkout) -> dict:
    """Upload a running workout. Returns the API response with workoutId."""
    return garmin.upload_running_workout(workout)


def schedule_workout(garmin: Garmin, workout_id: int, date: str) -> dict:
    """Schedule a workout to a calendar date.

    Args:
        workout_id: ID returned from upload_workout.
        date: Date string in YYYY-MM-DD format.
    """
    url = f"/workout-service/schedule/{workout_id}"
    payload = {"date": date}
    return garmin.garth.post("connectapi", url, json=payload, api=True).json()


def list_workouts(garmin: Garmin, limit: int = 20) -> list[dict]:
    """List workouts from the user's Garmin Connect account."""
    result = garmin.get_workouts(start=0, limit=limit)
    if isinstance(result, dict):
        return result.get("workouts", result.get("results", []))
    return result if isinstance(result, list) else []
