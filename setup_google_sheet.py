import gspread
from config import settings
from logger_setup import log


def setup_sheet_headers():
    """
    Writes a predefined set of headers to the first row of the Google Sheet
    and formats specific columns to use checkboxes.
    """
    log.info("--- Starting Google Sheet Setup ---")

    # --- 1. Define the headers you want to create ---
    headers = [
        settings.DATE_COLUMN_NAME,
        settings.TIME_COLUMN_NAME,
        settings.STATUS_COLUMN_NAME,
        settings.TEXT_COLUMN_NAME,
        settings.IMAGE_URLS_COLUMN_NAME,
        settings.VIDEO_URLS_COLUMN_NAME,
        settings.HASHTAGS_COLUMN_NAME,
        settings.HASHTAGS_WITH_TEXT_COLUMN_NAME,
        settings.DO_NOT_POST_MEDIA_ON_THREADS_COLUMN_NAME,
        settings.POST_ON_INSTAGRAM_COLUMN_NAME,
        settings.POST_ON_THREADS_COLUMN_NAME,
    ]

    # Define which columns should be formatted as checkboxes
    checkbox_columns = [
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
        worksheet.update("A1", [headers])
        log.info("✅ Successfully populated Google Sheet with headers.")

        # --- 4. Apply checkbox formatting ---
        log.info("Applying checkbox formatting to columns...")
        formatting_requests = []
        worksheet_id = worksheet.id

        for col_name in checkbox_columns:
            if col_name in headers:
                # Find the column index (0-based)
                col_index = headers.index(col_name)

                # Define the data validation rule for a checkbox
                validation_rule = {
                    "condition": {"type": "BOOLEAN"},
                    "strict": True,
                    "showCustomUi": True,
                }

                # Create the request payload to apply the rule to the entire column (except the header)
                # The API uses zero-based indexes directly, so no conversion is needed.
                request = {
                    "setDataValidation": {
                        "range": {
                            "sheetId": worksheet_id,
                            "startRowIndex": 1,  # Start from the second row
                            "startColumnIndex": col_index,
                            "endColumnIndex": col_index + 1,
                        },
                        "rule": validation_rule,
                    }
                }
                formatting_requests.append(request)

        # Send all formatting requests in a single batch update
        if formatting_requests:
            spreadsheet.batch_update({"requests": formatting_requests})
            log.info(f"✅ Successfully formatted columns as checkboxes.")

        log.info("Sheet setup is complete.")

    except gspread.exceptions.SpreadsheetNotFound:
        log.error(f"Error: Spreadsheet '{settings.GOOGLE_SHEET_NAME}' not found.")
    except gspread.exceptions.WorksheetNotFound:
        log.error(f"Error: Worksheet '{settings.WORKSHEET_NAME}' not found.")
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    setup_sheet_headers()
