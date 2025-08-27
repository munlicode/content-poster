from datetime import date
from dateutil import parser

from interfaces import IProcessor
from config import settings
from logger_setup import log


class TodayAndUnpublishedFilter(IProcessor):
    """Filters for posts that are for today and are not yet published."""

    def process(self, data: list) -> list:
        log.info("Filtering for all of today's unpublished posts...")
        today = date.today()

        pending_posts = []
        for item in data:
            raw_date = str(item.get(settings.DATE_COLUMN_NAME, "")).strip()
            if not raw_date:
                continue

            try:
                # Parse the date flexibly (handles dd.mm.yyyy, mm/dd/yyyy, etc.)
                parsed_date = parser.parse(raw_date, fuzzy=True, dayfirst=True).date()
            except (ValueError, TypeError):
                log.warning(f"Skipping item due to invalid date format: '{raw_date}'")
                continue

            if parsed_date != today:
                continue

            status = str(item.get(settings.STATUS_COLUMN_NAME, "")).lower()
            if status == settings.STATUS_OPTIONS["published"].lower():
                continue

            pending_posts.append(item)

        return pending_posts
