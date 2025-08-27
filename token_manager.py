import json
from datetime import datetime, timedelta
from logger_setup import log

TOKEN_FILE = "token_storage.json"


def load_token():
    """Loads the entire token data structure from the JSON file."""
    try:
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is empty, return a default structure
        return {"threads": {}, "instagram": {}}


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
    all_tokens = load_token()

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
    with open(TOKEN_FILE, "w") as f:
        json.dump(all_tokens, f, indent=4)

    log.info(
        f"Successfully saved new {platform} token. It expires on: {expiry_date.strftime('%Y-%m-%d')}"
    )
