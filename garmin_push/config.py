"""User configuration for garmin-push.

Loads pace zones and settings from ~/.garmin-push/config.yaml.
Falls back to defaults if no config file exists.
"""

from pathlib import Path

import yaml

from .models import DEFAULT_PACE_ZONES

CONFIG_DIR = Path.home() / ".garmin-push"
CONFIG_PATH = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG_YAML = """\
# garmin-push configuration
# Pace zones as [fast, slow] in min:sec per km
pace_zones:
  easy: ["6:00", "6:30"]
  moderate: ["5:20", "5:40"]
  tempo: ["4:40", "5:00"]
  threshold: ["4:20", "4:40"]
  interval: ["3:50", "4:10"]
  sprint: ["3:20", "3:40"]
"""


def load_config() -> dict[str, tuple[str, str]]:
    """Load pace zones from config file, merged with defaults.

    Returns a pace_zones dict mapping zone names to (slow, fast) pace tuples.
    """
    zones = dict(DEFAULT_PACE_ZONES)

    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            data = yaml.safe_load(f) or {}

        user_zones = data.get("pace_zones", {})
        for name, value in user_zones.items():
            if isinstance(value, (list, tuple)) and len(value) == 2:
                zones[name] = (str(value[0]), str(value[1]))

    return zones


def create_config() -> Path:
    """Create a starter config file at ~/.garmin-push/config.yaml.

    Returns the path to the created file.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(DEFAULT_CONFIG_YAML)
    return CONFIG_PATH
