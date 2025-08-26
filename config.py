from pydantic_settings import BaseSettings

from typing import Optional


class Settings(BaseSettings):

    CACHE_FILE_PATH: str = "post_cache.json"

    THREADS_API_VERSION: str = "v1.0"
    THREADS_API_BASE_URL: str = "https://graph.threads.net/"
    FACEBOOK_API_VERSION: str = "v23.0"
    FACEBOOK_API_BASE_URL: str = "https://graph.facebook.com/"

    THREADS_CLIENT_ID: str
    THREADS_CLIENT_SECRET: str

    # --- Google Sheets Settings ---
    # Follow a guide on "Google Cloud Service Account" to get this JSON file.
    # Place the file in the same directory as your project.
    GOOGLE_CREDENTIALS_FILE: str = "credentials.json"

    # The exact name of your Google Sheet document
    GOOGLE_SHEET_NAME: str = "aaa101"

    # The name of the specific tab (worksheet) inside the sheet
    WORKSHEET_NAME: str = "Sheet1"

    # --- Column Header Names ---
    # The names of the columns in your worksheet that contain the data.
    # IMPORTANT: Your Google Sheet must have columns with these exact names.
    DATE_COLUMN_NAME: str = "date"  # Expected format in sheet: YYYY-MM-DD
    TEXT_COLUMN_NAME: str = "text"  # The content to be posted
    TIME_COLUMN_NAME: str = "time"
    STATUS_COLUMN_NAME: str = "status"

    # --- Advanced Settings ---
    # A list of times (in 24-hour HH:MM format) to fetch fresh data from Google Sheets.
    # To fetch only once a day at 7 AM: FETCH_SCHEDULE = ["07:00"]
    # To fetch three times a day: FETCH_SCHEDULE = ["07:00", "12:00", "17:00"]
    FETCH_SCHEDULE: list[str] = ["08:00", "13:00", "16:51", "18:00", "21:39"]
    STATUS_OPTIONS: dict[str, str] = (
        {  # if Applyable means that it is used already, otherwise it means that it might be implemented
            "published": "Published",  # Applyable
            "draft": "Draft",  # Not Applyable --- Setted by user in case if he wants to set it as draft and do not publish until changed to None
            "pending": "Pending",  # Not Applyable --- To mark that task was accepted and awaits time of execution
            "error": "Error",  # Not Applyable --- In case of when errors will be handled
            "failed": "Failed",  # Applyable
            "cancelled": "Cancelled",  # Not Applyable --- Setted by user in case if he wants to cancel publishing
        }
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
