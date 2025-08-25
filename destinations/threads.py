from typing import Dict
import requests
from interfaces import IDestination
from logger_setup import log
from config import settings
import token_manager


class ThreadsDestination(IDestination):
    """A destination that posts content to Meta's Threads API."""

    def post(self, content: Dict) -> bool:
        """
        Publishes a text post to Threads using a two-step process:
        1. Create a media container with the text.
        2. Publish the container to the user's Threads feed.
        """
        token_data = token_manager.load_token()
        current_token = token_data.get("access_token")
        if not current_token:
            log.error("Could not load access token. Cannot post.")
            return False

        user_id = token_data.get("user_id")
        if not user_id:
            log.error("Could not find user id. Cannot post.")
            return False

        text_to_post = content.get(settings.TEXT_COLUMN_NAME)
        if not text_to_post:
            log.error("No text found in content item to post.")
            return False

        # --- Step 1: Create the media container ---
        # UPDATED ENDPOINT: Now uses '/threads'
        container_creation_url = f"{settings.THREADS_API_BASE_URL}{settings.THREADS_API_VERSION}/{user_id}/threads"
        container_payload = {
            "media_type": "TEXT",
            "text": text_to_post,
            "access_token": current_token,
        }

        try:
            log.info(
                f"Creating Threads media container for text: '{text_to_post[:30]}...'"
            )
            # The API documentation shows parameters in the URL, so we'll use `params` instead of `data`.
            container_response = requests.post(
                container_creation_url, params=container_payload
            )
            container_response.raise_for_status()
            container_data = container_response.json()
            container_id = container_data.get("id")
            if not container_id:
                log.error(
                    f"Failed to create media container. Response: {container_data}"
                )
                return False
        except requests.exceptions.RequestException as e:
            log.error(f"Error creating media container: {e}")
            log.error(
                f"Response body: {e.response.text if e.response else 'No response'}"
            )
            return False

        # --- Step 2: Publish the media container ---
        # UPDATED ENDPOINT: Now uses '/threads_publish'
        publish_url = f"{settings.THREADS_API_BASE_URL}{settings.THREADS_API_VERSION}/{settings.INSTAGRAM_USER_ID}/threads_publish"
        publish_payload = {
            "creation_id": container_id,
            "access_token": current_token,
        }

        try:
            log.info(f"Publishing container ID: {container_id}")
            # Using `params` here as well to match the documentation's cURL examples.
            publish_response = requests.post(publish_url, params=publish_payload)
            publish_response.raise_for_status()
            publish_data = publish_response.json()
            log.info(
                f"🚀 Successfully published to Threads! Post ID: {publish_data.get('id')}"
            )
            return True
        except requests.exceptions.RequestException as e:
            log.error(f"Error publishing media container: {e}")
            log.error(
                f"Response body: {e.response.text if e.response else 'No response'}"
            )
            return False
