import requests
import token_manager
from config import settings
from logger_setup import log

{
    "threads": {
        "access_token": "THAA6k4BBcKAJBUVJGWjZANRFMzT0hIRENhQVpTSE5nOHNzTmlONWpwazlwa3BnbmRWZAExVakt6UVpRbEh4a2djZAFBualBBNlZApY19BS0NsSmZAiMEpKVWs1Uno5cVN0dlJ5UVVQc0tHWXZAHRHl4YmtGZA2ZAyT2R2b05xX2hWbmpOOXFmdwZDZD",
        "expiry_date": "2025-10-26T23:13:31.092393",
        "user_id": "24714043398191525",
    },
    "instagram": {
        "access_token": "EAAzDnL2iKGYBPUocwx9wJRQnY2IgEK0qq0bnaR2gYOZAKYwguZCkIRZAfHd1Nu9NglageCN7J9HI34h39RLqvweSjr0mxoqj9NhcZACyU6LZAXi9bqCED0VklUGcKO6HeSzLcjhZAilBCDL2BEZAL6bISf9dY8khJDV0VZCfPJlBlv3VZBElRNii064yB1ZCGZB",
        "expiry_date": "2025-10-26T22:31:45.160148",
        "user_id": "17841448219722435",
    },
}


def exchange_and_save_token(platform: str):
    """
    Guides the user to provide a short-lived token for a platform,
    exchanges it for a long-lived token, and saves it.
    """
    log.info(f"\n--- Step 1: Provide credentials for {platform.upper()} ---")

    short_lived_token = input(
        f"Please paste the short-lived {platform.upper()} access token and press Enter: "
    ).strip()
    if not short_lived_token:
        log.error("A short-lived token is required. Aborting.")
        return False

    user_id = input(
        f"Please paste the {platform.upper()} User ID and press Enter: "
    ).strip()
    if not user_id:
        log.error("User ID is required. Aborting.")
        return False

    # --- Step 2: Exchange Short-Lived for a Long-Lived Token ---
    log.info(
        f"\n--- Step 2: Exchanging for a long-lived {platform.upper()} token... ---"
    )

    # The endpoint for exchanging tokens is the same for both platforms
    if platform == "instagram":
        exchange_url = f"{settings.FACEBOOK_API_BASE_URL}{settings.FACEBOOK_API_VERSION}/oauth/access_token"

        payload = {
            "grant_type": "fb_exchange_token",
            "client_id": settings.APP_CLIENT_ID,
            "client_secret": settings.APP_CLIENT_SECRET,
            "fb_exchange_token": short_lived_token,
        }
    elif platform == "threads":
        exchange_url = f"{settings.THREADS_API_BASE_URL}{settings.THREADS_API_VERSION}/access_token"
        payload = {
            "grant_type": "th_exchange_token",
            "client_secret": settings.APP_CLIENT_SECRET,
            "access_token": short_lived_token,
        }
    try:
        response = requests.get(exchange_url, params=payload)
        response.raise_for_status()
        new_token_data = response.json()

        long_lived_token = new_token_data.get("access_token")
        expires_in = new_token_data.get("expires_in")

        if not long_lived_token or not expires_in:
            log.error(f"Token exchange response was invalid: {new_token_data}")
            return False

        # Save the token to the correct part of the JSON file
        token_manager.save_token(platform, long_lived_token, expires_in, user_id)
        return True

    except requests.exceptions.RequestException as e:
        log.error(
            f"Failed to exchange token for {platform}. API Error: {e.response.text if e.response else e}"
        )
        return False


def main():
    """Main function to run the token generation flow for all platforms."""
    log.info("--- Starting Initial Token Generation ---")

    # Run the flow for Instagram
    if not exchange_and_save_token("instagram"):
        log.error(
            "\nCould not generate the Instagram token. Please check the error above and try again."
        )
        return

    # Run the flow for Threads
    if not exchange_and_save_token("threads"):
        log.error(
            "\nCould not generate the Threads token. Please check the error above and try again."
        )
        return

    log.info(
        "\n✅ All tokens have been successfully generated and saved to token_storage.json."
    )
    log.info("Your application is now ready to run.")


if __name__ == "__main__":
    main()
