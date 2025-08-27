from datetime import datetime
from dateutil import parser
import logging

from interfaces import IProcessor
from config import settings

log = logging.getLogger(__name__)


class TimeValidator(IProcessor):
    """From a list of posts, returns only those whose scheduled date/time has passed."""

    def process(self, data: list) -> list:
        log.info("Validating scheduled times...")
        now = datetime.now()
        posts_due = []

        for item in data:
            datetime_str = str(item.get(settings.TIME_COLUMN_NAME, "")).strip()
            if not datetime_str:
                log.warning("Skipping item with empty date/time field")
                continue

            try:
                # Parse flexibly any localized date/time string
                scheduled_dt = parser.parse(datetime_str, fuzzy=True, dayfirst=True)

                # Only add if scheduled time has passed
                if now >= scheduled_dt:
                    posts_due.append(item)

            except (ValueError, TypeError) as e:
                log.warning(
                    f"Skipping item due to invalid or unrecognized date/time format '{datetime_str}': {e}"
                )
                continue

        return posts_due
