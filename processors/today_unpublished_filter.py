from datetime import date
from interfaces import IProcessor
from config import settings
from logger_setup import log


class TodayAndUnpublishedFilter(IProcessor):
    """Filters for posts that are for today and are not yet published."""

    def process(self, data: list) -> list:
        log.info("Filtering for all of today's unpublished posts...")
        today_str = str(date.today())

        pending_posts = []
        for item in data:
            if str(item.get(settings.DATE_COLUMN_NAME, "")) != today_str:
                continue
            if (
                str(item.get(settings.STATUS_COLUMN_NAME, "")).lower()
                == settings.STATUS_OPTIONS["published"].lower()
            ):
                continue
            pending_posts.append(item)

        return pending_posts
