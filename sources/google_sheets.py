from typing import List, Dict
import gspread
from interfaces import IDataSource
from config import settings
from logger_setup import log


class GoogleSheetsSource(IDataSource):
    """Fetches data from a specified Google Sheet and can update it."""

    def __init__(self):
        try:
            self.client = gspread.service_account(
                filename=settings.GOOGLE_CREDENTIALS_FILE
            )
            self.sheet = self.client.open(settings.GOOGLE_SHEET_NAME).worksheet(
                settings.WORKSHEET_NAME
            )
            # Get the column headers to find the status column number later
            self.headers = self.sheet.row_values(1)
        except Exception as e:
            log.error(f"Could not connect to Google Sheet. Details: {e}")
            self.client = None
            self.sheet = None

    def get_data(self) -> List[Dict]:
        """Gets all rows and adds a 'row_number' to each for later updates."""
        if not self.sheet:
            return []

        log.info(
            f"Successfully connected to '{settings.GOOGLE_SHEET_NAME}'. Fetching data..."
        )
        records = self.sheet.get_all_records()

        # Add the original row number to each record
        for i, record in enumerate(records):
            record["row_number"] = (
                i + 2
            )  # +2 because sheets are 1-indexed and we skip the header

        return records

    def update_status(self, row_number: int, status_text: str) -> bool:
        """Finds the 'status' column and updates the cell for a given row."""
        if not self.sheet:
            return False

        try:
            # Find which column number corresponds to the status header
            status_col_index = self.headers.index(settings.STATUS_COLUMN_NAME) + 1
            self.sheet.update_cell(row_number, status_col_index, status_text)
            log.info(f"Updated row {row_number} status to '{status_text}'.")
            return True
        except ValueError:
            log.info(
                f"ERROR: Status column '{settings.STATUS_COLUMN_NAME}' not found in sheet."
            )
            return False
        except Exception as e:
            log.info(f"ERROR: Could not update sheet. Details: {e}")
            return False
