import requests
from datetime import datetime, timedelta
import token_manager
from config import settings
from logger_setup import log


def refresh_platform_token(platform: str):
    """
    Checks if a platform's access token is expiring soon and refreshes it if necessary.
    Handles differences between Instagram and Threads APIs.
    """
    log.info(f"--- Starting Token Refresh Check for {platform.upper()} ---")

    all_tokens = token_manager.load_token()
    token_data = all_tokens.get(platform, {})

    access_token = token_data.get("access_token")
    expiry_date_str = token_data.get("expiry_date")
    user_id = token_data.get("user_id")

    if not all([access_token, expiry_date_str, user_id]):
        log.error(f"Token data for {platform} is incomplete. Cannot refresh.")
        return

    # Check if the token expires within the next 7 days
    expiry_date = datetime.fromisoformat(expiry_date_str)
    if expiry_date > (datetime.now() + timedelta(days=7)):
        log.info(
            f"{platform.upper()} token is not expiring soon (expires on {expiry_date.strftime('%Y-%m-%d')}). No refresh needed."
        )
        return

    log.warning(f"{platform.upper()} token is expiring soon. Attempting to refresh...")

    # --- Set API parameters based on the platform ---
    if platform == "instagram":
        # Instagram uses the Graph API and 'ig_refresh_token'
        refresh_url = f"{settings.FACEBOOK_API_BASE_URL}{settings.FACEBOOK_API_VERSION}/oauth/access_token"

        payload = {
            "grant_type": "fb_exchange_token",
            "client_id": settings.APP_CLIENT_ID,
            "client_secret": settings.APP_CLIENT_SECRET,
            "fb_exchange_token": access_token,
        }
    elif platform == "threads":
        # Threads has its own endpoint and 'th_refresh_token'
        refresh_url = f"{settings.THREADS_API_BASE_URL}{settings.THREADS_API_VERSION}/refresh_access_token"
        payload = {"grant_type": "th_refresh_token", "access_token": access_token}
    else:
        log.error(f"Unknown platform for token refresh: {platform}")
        return

    # --- Make the API call to refresh the token ---
    try:
        response = requests.get(refresh_url, params=payload)
        response.raise_for_status()
        new_token_data = response.json()

        new_token = new_token_data.get("access_token")
        expires_in = new_token_data.get("expires_in")

        if not new_token or not expires_in:
            log.error(f"Refresh response for {platform} was invalid: {new_token_data}")
            return

        # Save the refreshed token using the updated token_manager
        token_manager.save_token(platform, new_token, expires_in, user_id)
        log.info(
            f"✅ {platform.upper()} token has been successfully refreshed and saved."
        )

    except requests.exceptions.RequestException as e:
        log.error(
            f"Failed to refresh {platform} token. API Error: {e.response.text if e.response else e}"
        )


if __name__ == "__main__":
    # Run the refresh logic for both platforms
    refresh_platform_token("instagram")
    refresh_platform_token("threads")
