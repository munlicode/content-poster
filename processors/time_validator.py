from datetime import datetime
from interfaces import IProcessor
from config import settings
from logger_setup import log


class TimeValidator(IProcessor):
    """From a list of posts, returns only those whose scheduled time has passed."""

    def process(self, data: list) -> list:
        log.info("Validating scheduled times...")
        now = datetime.now()
        posts_due = []

        today_str = now.strftime("%Y-%m-%d")

        for item in data:
            post_time_str = str(item.get(settings.TIME_COLUMN_NAME, ""))
            try:
                # Combine today's date with the post's time to create a datetime object
                scheduled_time = datetime.strptime(
                    f"{today_str} {post_time_str}", "%Y-%m-%d %H:%M"
                )

                # This is the critical filter: only add the post if its time is now or in the past
                if now >= scheduled_time:
                    posts_due.append(item)
            except ValueError:
                # Handle cases where the time format in the sheet is wrong
                log.warning(
                    f"Skipping item due to invalid time format: '{post_time_str}'"
                )
                continue

        return posts_due
