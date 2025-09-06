import requests
import token_manager
from config import settings
from logger_setup import log


def get_long_lived_token_data(platform: str) -> dict | None:
    """
    Guides the user to provide a short-lived token and exchanges it for long-lived token data.
    Returns a dictionary with token data on success, None on failure.
    """
    log.info(f"\n--- Enter credentials for {platform.upper()} ---")
    short_lived_token = input(
        f"Paste the short-lived {platform.upper()} access token and press Enter: "
    ).strip()
    if not short_lived_token:
        log.error("Token is required. Aborting.")
        return None

    user_id = input(f"Paste the {platform.upper()} User ID and press Enter: ").strip()
    if not user_id:
        log.error("User ID is required. Aborting.")
        return None

    log.info(f"Exchanging for a long-lived {platform.upper()} token...")

    payload = {}
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
        token_data = response.json()

        long_lived_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in")

        if not long_lived_token or not expires_in:
            log.error(f"Token exchange response was invalid: {token_data}")
            return None

        return {
            "access_token": long_lived_token,
            "expiry_date": token_manager.calculate_expiry_date(expires_in),
            "user_id": user_id,
        }
    except requests.exceptions.RequestException as e:
        log.error(
            f"Failed to exchange token. API Error: {e.response.text if e.response else e}"
        )
        return None


def main():
    """Main function to run the interactive token generation flow."""
    all_tokens = token_manager.load_tokens()

    print("--- Social Media Token Manager ---")

    # --- Step 1: Choose Action ---
    mode = ""
    while mode not in ["1", "2"]:
        mode = input(
            "What would you like to do?\n (1) Add a new account profile\n (2) Update an existing profile\nChoose (1 or 2): "
        ).strip()

    if mode == "2":
        if not all_tokens:
            log.warning("No profiles exist yet. Switching to 'Add' mode.")
            mode = "1"
        else:
            print("\nExisting profiles:", ", ".join(all_tokens.keys()))

    # --- Step 2: Loop for Profile Input ---
    while True:
        action_word = "update" if mode == "2" else "add"
        profile_name = input(
            f"\nEnter the profile name to {action_word} (e.g., 'Page1', 'personal_acct') [Press Enter to finish]: "
        ).strip()

        if not profile_name:
            break

        if mode == "2" and profile_name not in all_tokens:
            log.error(
                f"Profile '{profile_name}' does not exist. Please enter an existing profile name."
            )
            continue

        if mode == "1" and profile_name in all_tokens:
            overwrite = (
                input(f"Profile '{profile_name}' already exists. Overwrite? (y/n): ")
                .strip()
                .lower()
            )
            if overwrite != "y":
                continue

        log.info(f"\n--- Configuring profile: '{profile_name}' ---")

        # --- Step 3: Get Tokens for the Profile ---
        instagram_data = get_long_lived_token_data("instagram")
        if not instagram_data:
            log.error(
                f"Could not get Instagram token for '{profile_name}'. Skipping this profile."
            )
            continue

        threads_data = {}
        get_long_lived_token_data("threads")
        if not threads_data:
            log.error(
                f"Could not get Threads token for '{profile_name}'. Skipping this profile."
            )
            continue

        all_tokens[profile_name] = {
            "instagram": instagram_data,
            "threads": threads_data,
        }
        log.info(f"✅ Successfully configured profile '{profile_name}'.")

    # --- Step 4: Save All Changes ---
    if all_tokens:
        token_manager.save_tokens(all_tokens)
        log.info("\nAll changes have been saved.")
    else:
        log.info("\nNo changes were made.")


if __name__ == "__main__":
    main()
