import json
from datetime import datetime, timedelta
from logger_setup import log
from config import settings


def load_tokens() -> dict:
    """
    Loads the entire token storage dictionary from the JSON file.
    Returns an empty dictionary if the file doesn't exist.
    """
    try:
        with open(settings.TOKEN_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        log.error(f"Could not decode JSON from {settings.TOKEN_FILE}. Starting fresh.")
        return {}


def save_tokens(all_tokens: dict):
    """
    Saves the entire token storage dictionary to the JSON file.
    """
    try:
        with open(settings.TOKEN_FILE, "w") as f:
            json.dump(all_tokens, f, indent=4)
        log.info(f"Successfully saved tokens to {settings.TOKEN_FILE}")
    except IOError as e:
        log.error(f"Could not write tokens to file: {e}")


def calculate_expiry_date(expires_in_seconds: int) -> str:
    """
    Calculates the token's absolute expiry date from a 'seconds until expiry' value.
    """
    return (datetime.now() + timedelta(seconds=expires_in_seconds)).isoformat()


def save_token(platform: str, token: str, expires_in: int, user_id: str):
    """
    Saves a new token for a specific platform (threads or instagram).
    """
    if platform not in ["threads", "instagram"]:
        log.error(
            f"Invalid platform specified: {platform}. Must be 'threads' or 'instagram'."
        )
        return

    # Load the entire current token data
    all_tokens = load_tokens()

    # Calculate the new expiry date
    expiry_date = datetime.now() + timedelta(seconds=expires_in)

    # Create the new token data for the specific platform
    new_token_data = {
        "access_token": token,
        "expiry_date": expiry_date.isoformat(),
        "user_id": user_id,
    }

    # Update the data for the specified platform
    all_tokens[platform] = new_token_data

    # Save the entire updated structure back to the file
    with open(settings.TOKEN_FILE, "w") as f:
        json.dump(all_tokens, f, indent=4)

    log.info(
        f"Successfully saved new {platform} token. It expires on: {expiry_date.strftime('%Y-%m-%d')}"
    )
