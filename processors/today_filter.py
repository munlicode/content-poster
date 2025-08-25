from typing import List, Dict
from datetime import date
from interfaces import IProcessor
from config import settings
from logger_setup import log


class TodayFilter(IProcessor):
    """Filters a list of data to include only items with today's date."""

    def process(self, data: List[Dict]) -> List[Dict]:
        """
        Filters data based on the date column.
        Expects date format in the sheet to be 'YYYY-MM-DD'.
        """
        today_str = date.today().isoformat()  # Gets date in 'YYYY-MM-DD' format
        log.info(f"Filtering for posts with date: {today_str}")

        filtered_data = []
        for item in data:
            # gspread might read dates as strings, so we compare strings.
            if str(item.get(settings.DATE_COLUMN_NAME)) == today_str:
                filtered_data.append(item)

        return filtered_data
