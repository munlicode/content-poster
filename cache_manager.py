import json
from datetime import datetime, time
from config import settings
from logger_setup import log


def load_cache():
    """Loads the cache from the file."""
    try:
        with open(settings.CACHE_FILE_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(posts_to_cache: list):
    """Saves the list of posts and the current time as the last_fetch_time."""
    cache_data = {
        "last_fetch_datetime": datetime.now().isoformat(),
        "pending_posts": posts_to_cache,
    }
    with open(settings.CACHE_FILE_PATH, "w") as f:
        json.dump(cache_data, f, indent=4)
    log.info(f"Saved {len(posts_to_cache)} posts to local cache.")


def should_fetch_fresh_data(last_fetch_str: str) -> bool:
    """
    Decides whether to fetch fresh data based on the schedule in config.py.
    Returns True if a scheduled fetch time has passed since the last fetch.
    """
    if not last_fetch_str:
        log.info("No last fetch time found. A fresh fetch is required.")
        return True

    now = datetime.now()
    last_fetch_dt = datetime.fromisoformat(last_fetch_str)

    # Check if a new day has started since the last fetch
    if now.date() > last_fetch_dt.date():
        log.info("New day has started. A fresh fetch is required.")
        return True
    log.info(f"FETCH_SCHEDULE: {settings.FETCH_SCHEDULE}")
    # Check if any scheduled time has passed since the last fetch
    for time_str in settings.FETCH_SCHEDULE:
        scheduled_time = datetime.strptime(time_str, "%H:%M").time()
        # Create a datetime object for today's scheduled time
        scheduled_dt = now.replace(
            hour=scheduled_time.hour,
            minute=scheduled_time.minute,
            second=0,
            microsecond=0,
        )

        # If a scheduled time is between the last fetch and now, we should fetch.
        if last_fetch_dt < scheduled_dt <= now:
            log.info(
                f"Scheduled fetch time {time_str} has passed. A fresh fetch is required."
            )
            return True

    return False
