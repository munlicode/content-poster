import requests
import token_manager
from config import settings
from logger_setup import log


def generate_and_save_tokens():
    """Guides the user through the full OAuth flow to get and save a long-lived token."""

    # --- Step 1: Get Authorization Code ---
    access_token = input(
        "\nPlease paste the 'access_token' from `Access Token` field and press Enter: "
    ).strip()

    if not access_token:
        log.error("Authorization code is required. Aborting.")
        return

    user_id = input(
        "\nPlease paste the 'App-Scoped User ID' from `Access Token Debugger -> Access Token Info` and press Enter: "
    ).strip()

    if not user_id:
        log.error("User ID is required. Aborting.")
        return

    # --- Step 2: Exchange Short-Lived for a Long-Lived Token ---
    log.info("\n--- Step 2: Exchanging code for a long-lived token... ---")
    refresh_url = f"{settings.THREADS_API_BASE_URL}{settings.THREADS_API_VERSION}/refresh_access_token"
    payload = {"grant_type": "th_refresh_token", "access_token": access_token}

    try:
        response = requests.get(refresh_url, params=payload)
        response.raise_for_status()
        new_token_data = response.json()

        long_lived_token = new_token_data.get("access_token")
        expires_in = new_token_data.get("expires_in")

        if not long_lived_token or not expires_in:
            log.error(f"Refresh response was invalid: {new_token_data}")
            return

        token_manager.save_token(long_lived_token, expires_in, user_id)
        log.info(
            "Your long-lived access token and user ID have been saved to token_storage.json."
        )
        log.info("Your application is now ready to run.")

    except requests.exceptions.RequestException as e:
        log.error(
            f"Failed to refresh token. API Error: {e.response.text if e.response else e}"
        )
        return


if __name__ == "__main__":
    generate_and_save_tokens()
