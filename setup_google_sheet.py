import gspread
from config import settings
from logger_setup import log


def setup_sheet_headers():
    """
    Writes a predefined set of headers to the first row of the Google Sheet.
    """
    log.info("--- Starting Google Sheet Setup ---")

    # --- 1. Define the headers you want to create ---
    headers = [
        settings.DATE_COLUMN_NAME,
        settings.TEXT_COLUMN_NAME,
        settings.TIME_COLUMN_NAME,
        settings.STATUS_COLUMN_NAME,
        settings.IMAGE_URLS_COLUMN_NAME,
        settings.VIDEO_URLS_COLUMN_NAME,
        settings.HASHTAGS_COLUMN_NAME,
        settings.HASHTAGS_WITH_TEXT_COLUMN_NAME,
        settings.DO_NOT_POST_MEDIA_ON_THREADS_COLUMN_NAME,
        settings.POST_ON_INSTAGRAM_COLUMN_NAME,
        settings.POST_ON_THREADS_COLUMN_NAME,
    ]

    try:
        # --- 2. Authenticate and open the worksheet ---
        log.info("Authenticating with Google Service Account...")
        gc = gspread.service_account(filename="credentials.json")

        log.info(f"Opening Google Sheet: '{settings.GOOGLE_SHEET_NAME}'")
        spreadsheet = gc.open(settings.GOOGLE_SHEET_NAME)

        log.info(f"Accessing worksheet: '{settings.WORKSHEET_NAME}'")
        worksheet = spreadsheet.worksheet(settings.WORKSHEET_NAME)

        # --- 3. Write the headers to the first row ---
        log.info("Writing headers to the first row...")
        # The [headers] is to ensure it's treated as a single row
        worksheet.update("A1", [headers])

        log.info("✅ Successfully populated Google Sheet with headers.")
        log.info("Sheet is ready for content.")

    except gspread.exceptions.SpreadsheetNotFound:
        log.error(f"Error: Spreadsheet '{settings.GOOGLE_SHEET_NAME}' not found.")
        log.error(
            "Please ensure the name in your .env file is correct and you've shared the sheet with the service account."
        )
    except gspread.exceptions.WorksheetNotFound:
        log.error(
            f"Error: Worksheet '{settings.WORKSHEET_NAME}' not found in the spreadsheet."
        )
        log.error("Please check the WORKSHEET_NAME in your .env file.")
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    setup_sheet_headers()
