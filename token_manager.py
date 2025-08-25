import json
from datetime import datetime, timedelta
from logger_setup import log

TOKEN_FILE = "token_storage.json"


def load_token():
    """Loads the token data from the JSON file."""
    try:
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_token(token: str, expires_in: int):
    """Saves a new token and calculates its expiry date."""
    expiry_date = datetime.now() + timedelta(seconds=expires_in)
    token_data = {"access_token": token, "expiry_date": expiry_date.isoformat()}
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=4)
    log.info(
        f"Successfully saved new token. It expires on: {expiry_date.strftime('%Y-%m-%d')}"
    )
