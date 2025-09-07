import requests
from datetime import datetime, timedelta
import token_manager
from config import settings
from logger_setup import log


def refresh_platform_token():
    """
    Checks if a platform's access token is expiring soon and refreshes it if necessary.
    Handles differences between Instagram and Threads APIs.
    """
    log.info(f"--- Starting Token Refresh Check ---")

    all_tokens = token_manager.load_tokens()
    refreshed_tokens = {}
    for sheet_name, sheet_data in all_tokens.items():
        refreshed_worksheets_data = {}

        for worksheet_name, worksheet_data in sheet_data.items():
            refreshed_platform_tokens = {}
            for platform, token_data in worksheet_data.items():
                access_token = token_data.get("access_token")
                expiry_date_str = token_data.get("expiry_date")
                user_id = token_data.get("user_id")

                if not all([access_token, expiry_date_str, user_id]):
                    log.error(
                        f"Token data for {platform} is incomplete. Cannot refresh."
                    )
                    refreshed_platform_tokens.setdefault(platform, token_data)
                    continue

                # Check if the token expires within the next 7 days
                expiry_date = datetime.fromisoformat(expiry_date_str)
                if expiry_date > (datetime.now() + timedelta(days=7)):
                    log.info(
                        f"{platform.upper()} token is not expiring soon (expires on {expiry_date.strftime('%Y-%m-%d')}). No refresh needed."
                    )
                    refreshed_platform_tokens.setdefault(platform, token_data)
                    continue

                log.warning(
                    f"{platform.upper()} token is expiring soon. Attempting to refresh..."
                )

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
                    payload = {
                        "grant_type": "th_refresh_token",
                        "access_token": access_token,
                    }
                else:
                    log.error(f"Unknown platform for token refresh: {platform}")
                    refreshed_platform_tokens.setdefault(platform, token_data)
                    continue

                # --- Make the API call to refresh the token ---
                try:
                    response = requests.get(refresh_url, params=payload)
                    response.raise_for_status()
                    new_token_data = response.json()

                    new_token = new_token_data.get("access_token")
                    expires_in = new_token_data.get("expires_in")

                    if not new_token or not expires_in:
                        log.error(
                            f"Refresh response for {platform} was invalid: {new_token_data}"
                        )
                        refreshed_platform_tokens.setdefault(platform, token_data)
                        continue
                    expires_at = token_manager.calculate_expiry_date(expires_in)
                    refreshed_token_data = {
                        "access_token": new_token,
                        "user_id": user_id,
                        "expiry_date": expires_at,
                    }
                    refreshed_platform_tokens.setdefault(platform, refreshed_token_data)

                except requests.exceptions.RequestException as e:
                    log.error(
                        f"Failed to refresh {platform} token. API Error: {e.response.text if e.response else e}"
                    )
            refreshed_worksheets_data.setdefault(
                worksheet_name, refreshed_platform_tokens
            )

        # Save the refreshed token using the updated token_manager
        refreshed_tokens.setdefault(sheet_name, refreshed_worksheets_data)
    token_manager.save_tokens(refreshed_tokens)
    log.info(f"✅ Tokens has been successfully refreshed and saved.")


if __name__ == "__main__":
    # Run the refresh logic for both platforms
    refresh_platform_token()
