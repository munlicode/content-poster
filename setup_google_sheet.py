import gspread
from config import settings
from logger_setup import log


def _index_to_col_letter(index: int) -> str:
    """Converts a 0-based column index to its A1 letter."""
    if index < 26:
        return chr(65 + index)
    return ""  # Simple version for A-Z


def setup_sheet_headers():
    """
    Writes headers and applies data validation rules using universal English/US-locale formulas.
    """
    log.info("--- Starting Google Sheet Setup ---")

    headers = [
        settings.DATE_COLUMN_NAME,
        settings.TIME_COLUMN_NAME,
        settings.STATUS_COLUMN_NAME,
        settings.TEXT_COLUMN_NAME,
        settings.HASHTAGS_COLUMN_NAME,
        settings.HASHTAGS_IN_CAPTION_COLUMN_NAME,
        settings.THREADS_TEXT_ONLY_COLUMN_NAME,
        settings.POST_ON_INSTAGRAM_COLUMN_NAME,
        settings.POST_ON_THREADS_COLUMN_NAME,
        settings.LOCAL_IMAGE_PATH_COLUMN_NAME,
        settings.LOCAL_VIDEO_PATH_COLUMN_NAME,
        settings.IMAGE_URLS_COLUMN_NAME,
        settings.VIDEO_URLS_COLUMN_NAME,
    ]

    # --- 1. Define columns for specific formatting ---
    checkbox_columns = [
        settings.HASHTAGS_IN_CAPTION_COLUMN_NAME,
        settings.THREADS_TEXT_ONLY_COLUMN_NAME,
        settings.POST_ON_INSTAGRAM_COLUMN_NAME,
        settings.POST_ON_THREADS_COLUMN_NAME,
    ]
    date_columns = [settings.DATE_COLUMN_NAME]
    time_columns = [settings.TIME_COLUMN_NAME]
    text_limit_columns = [settings.TEXT_COLUMN_NAME]

    try:
        # --- 2. Authenticate and open the worksheet ---
        log.info("Authenticating with Google Service Account...")
        gc = gspread.service_account(filename=settings.GOOGLE_CREDENTIALS_FILE)
        spreadsheet = gc.open(settings.GOOGLE_SHEET_NAME)
        worksheet = spreadsheet.worksheet(settings.WORKSHEET_NAME)

        # --- 3. Write the headers to the first row ---
        log.info("Writing headers to the first row...")
        worksheet.update(range_name="A1", values=[headers])
        log.info("✅ Successfully populated Google Sheet with headers.")

        # --- 4. Apply all data validation and formatting in one batch ---
        log.info("Applying data validation and formatting rules...")
        formatting_requests = []
        worksheet_id = worksheet.id

        # Helper function to create a validation request
        def create_validation_request(col_name, rule):
            if col_name in headers:
                col_index = headers.index(col_name)
                return {
                    "setDataValidation": {
                        "range": {
                            "sheetId": worksheet_id,
                            "startRowIndex": 1,
                            "startColumnIndex": col_index,
                            "endColumnIndex": col_index + 1,
                        },
                        "rule": rule,
                    }
                }
            return None

        # Checkbox rule
        for col in checkbox_columns:
            req = create_validation_request(
                col,
                {
                    "condition": {"type": "BOOLEAN"},
                    "strict": True,
                    "showCustomUi": True,
                },
            )
            if req:
                formatting_requests.append(req)

        # --- THIS IS THE FIX ---
        # Date validation using a combination of basic, reliable functions
        for col in date_columns:
            if col in headers:
                col_index = headers.index(col)
                col_letter = _index_to_col_letter(col_index)

                # This formula manually checks the format and validity of the date string
                formula = (
                    f"=OR(ISBLANK({col_letter}2), AND(LEN({col_letter}2)=10, "
                    f'MID({col_letter}2,5,1)="-", MID({col_letter}2,8,1)="-", '
                    f"ISNUMBER(DATEVALUE({col_letter}2))))"
                )

                rule = {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": formula}],
                    },
                    "strict": True,
                    "inputMessage": "Enter a date in YYYY-MM-DD format only.",
                }
                req = create_validation_request(col, rule)
                if req:
                    formatting_requests.append(req)

        # Time validation
        for col in time_columns:
            if col in headers:
                col_index = headers.index(col)
                col_letter = _index_to_col_letter(col_index)
                formula = f"=OR(ISBLANK({col_letter}2), AND(ISNUMBER({col_letter}2), {col_letter}2>=0, {col_letter}2<1))"
                rule = {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": formula}],
                    },
                    "strict": True,
                    "inputMessage": "Please enter a valid time (e.g., 14:30).",
                }
                req = create_validation_request(col, rule)
                if req:
                    formatting_requests.append(req)

        # Text length limit
        for col in text_limit_columns:
            if col in headers:
                col_index = headers.index(col)
                col_letter = _index_to_col_letter(col_index)
                formula = f"=LEN({col_letter}2) <= 500"
                rule = {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{"userEnteredValue": formula}],
                    },
                    "strict": False,
                    "inputMessage": "Text should be 500 characters or less.",
                }
                req = create_validation_request(col, rule)
                if req:
                    formatting_requests.append(req)

        # Send all formatting requests in a single batch update
        if formatting_requests:
            spreadsheet.batch_update({"requests": formatting_requests})
            log.info("✅ Successfully applied all formatting rules.")

        log.info("Sheet setup is complete.")

    except gspread.exceptions.SpreadsheetNotFound:
        log.error(f"Error: Spreadsheet '{settings.GOOGLE_SHEET_NAME}' not found.")
    except gspread.exceptions.WorksheetNotFound:
        log.error(f"Error: Worksheet '{settings.WORKSHEET_NAME}' not found.")
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    setup_sheet_headers()
