import requests
from datetime import datetime, timedelta
import token_manager
from config import settings
from logger_setup import log


def refresh_the_token():
    """
    Checks if the current access token is expiring soon and refreshes it if necessary.
    """
    log.info("--- Starting Token Refresh Check ---")

    token_data = token_manager.load_token()
    access_token = token_data.get("access_token")
    expiry_date_str = token_data.get("expiry_date")
    user_id = token_data.get("user_id")

    if not access_token or not expiry_date_str:
        log.error("Access token or expiry date not found in storage. Cannot refresh.")
        return

    # Check if the token expires within the next 7 days
    expiry_date = datetime.fromisoformat(expiry_date_str)
    if expiry_date > (datetime.now() + timedelta(days=7)):
        log.info(
            f"Token is not expiring soon (expires on {expiry_date.strftime('%Y-%m-%d')}). No refresh needed."
        )
        return

    log.warning(f"Token is expiring soon. Attempting to refresh...")

    # --- Make the API call to refresh the token ---
    refresh_url = f"{settings.THREADS_API_BASE_URL}{settings.THREADS_API_VERSION}/refresh_access_token"
    payload = {"grant_type": "th_refresh_token", "access_token": access_token}

    try:
        response = requests.get(refresh_url, params=payload)
        response.raise_for_status()
        new_token_data = response.json()

        new_token = new_token_data.get("access_token")
        expires_in = new_token_data.get("expires_in")

        if not new_token or not expires_in:
            log.error(f"Refresh response was invalid: {new_token_data}")
            return

        token_manager.save_token(new_token, expires_in, user_id)
        log.info("✅ Token has been successfully refreshed and saved.")

    except requests.exceptions.RequestException as e:
        log.error(
            f"Failed to refresh token. API Error: {e.response.text if e.response else e}"
        )


if __name__ == "__main__":
    refresh_the_token()
