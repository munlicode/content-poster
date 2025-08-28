import re
import time
from typing import Dict, Optional, List
import requests
from interfaces import IDestination
from logger_setup import log
from config import settings
import token_manager
from processors.parse_clean_urls import parse_and_clean_urls


class ThreadsDestination(IDestination):
    """A destination that posts content to Meta's Threads API."""

    def __init__(self):
        all_tokens = token_manager.load_token()
        token_data = all_tokens.get("threads", {})

        self.user_id = token_data.get("user_id")
        self.access_token = token_data.get("access_token")
        self.base_url = f"{settings.THREADS_API_BASE_URL}{settings.THREADS_API_VERSION}"

    # NEW: Helper function to correctly format hashtags.
    def _format_hashtags(self, hashtags: Optional[str]) -> Optional[str]:
        """Formats a comma-separated string of hashtags into a space-separated list."""
        if not hashtags:
            return None
        return hashtags  # FIXME: COMMENTING OUT hastags formating
        formatted_tags = []
        for tag in hashtags.split(","):
            tag = tag.strip()
            if tag:
                # Add '#' if it's not already there, but don't add a second one.
                if not tag.startswith("#"):
                    formatted_tags.append(f"#{tag}")
                else:
                    formatted_tags.append(tag)
        return " ".join(formatted_tags)

    # NEW: Modified caption builder to handle the flag.
    def _build_caption(
        self, text: Optional[str], hashtags: Optional[str], include_hashtags: bool
    ) -> str:
        """Combines text and optionally hashtags into a single caption string."""
        caption_parts: List[str] = []
        if text:
            caption_parts.append(text.strip())

        if include_hashtags:
            formatted_hashtags = self._format_hashtags(hashtags)
            if formatted_hashtags:
                caption_parts.append(formatted_hashtags)

        return "\n\n".join(caption_parts)

    def _post_reply(self, original_post_id: str, reply_text: str) -> bool:
        """Posts a reply to a given Threads post ID using the required two-step process."""
        log.info(
            f"Attempting to post hashtags as a reply to Thread ID: {original_post_id}"
        )

        # Reusing token data from the class instance
        access_token = self.access_token
        user_id = self.user_id

        # --- Step 1: Create a Reply Container ---
        container_endpoint = f"{self.base_url}/{user_id}/threads"
        container_payload = {
            "access_token": access_token,
            "media_type": "TEXT",
            "text": reply_text,
            "reply_to_id": original_post_id,
        }
        creation_id = None
        try:
            log.info("Reply Step 1: Creating reply container...")
            response = requests.post(container_endpoint, params=container_payload)
            response.raise_for_status()
            response_data = response.json()
            creation_id = response_data.get("id")
            if not creation_id:
                log.error(
                    f"Failed to create reply container. Response: {response_data}"
                )
                return False
            log.info(f"Reply container created. Creation ID: {creation_id}")

        except requests.exceptions.RequestException as e:
            log.error(
                f"Failed to create reply container. API Error: {e.response.text if e.response else e}"
            )
            return False

        # --- Step 2: Publish the Reply Container ---
        # The documentation recommends waiting for server processing
        time.sleep(3)

        publish_endpoint = f"{self.base_url}/{user_id}/threads_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": access_token,
        }
        try:
            log.info(f"Reply Step 2: Publishing reply container {creation_id}...")
            response = requests.post(publish_endpoint, params=publish_payload)
            response.raise_for_status()
            log.info("✅ Successfully posted hashtags as a reply.")
            return True
        except requests.exceptions.RequestException as e:
            log.error(
                f"Failed to publish reply container. API Error: {e.response.text if e.response else e}"
            )
            return False

    def post(self, content: Dict) -> bool:
        """Publishes content to Threads using a two-step create and publish flow."""
        if not all([self.user_id, self.access_token]):
            log.error("Missing user_id or access_token. Cannot post to Threads.")
            return False

        # --- 1. Prepare Content ---
        text = content.get(settings.TEXT_COLUMN_NAME)
        hashtags = content.get(settings.HASHTAGS_COLUMN_NAME)

        post_hashtags_in_caption = (
            str(content.get(settings.HASHTAGS_IN_CAPTION_COLUMN_NAME, ""))
            .strip()
            .upper()
            == "TRUE"
        )
        text_only = (
            str(content.get(settings.THREADS_TEXT_ONLY_COLUMN_NAME, "")).strip().upper()
            == "TRUE"
        )

        # Clean up each resulting URL and filter out any empty strings
        image_urls = parse_and_clean_urls(
            content.get(settings.IMAGE_URLS_COLUMN_NAME, "")
        )

        video_urls = parse_and_clean_urls(
            content.get(settings.VIDEO_URLS_COLUMN_NAME, "")
        )

        # But you only ever use the FIRST item from the list
        image_url = (
            image_urls[0].strip() if image_urls and image_urls[0].strip() else None
        )
        video_url = (
            video_urls[0].strip() if video_urls and video_urls[0].strip() else None
        )

        if text_only:
            image_url, video_url = None, None

        caption = self._build_caption(
            text, hashtags, include_hashtags=post_hashtags_in_caption
        )

        if not caption and not image_url and not video_url:
            log.error("No content (text, image, or video) found to post to Threads.")
            return False

        # --- 2. Step 1: Create Media Container ---
        creation_id = None
        container_endpoint = f"{self.base_url}/{self.user_id}/threads"
        payload = {"access_token": self.access_token}

        if image_url:
            payload.update({"media_type": "IMAGE", "image_url": image_url})
        elif video_url:
            payload.update({"media_type": "VIDEO", "video_url": video_url})
        else:
            payload.update({"media_type": "TEXT"})

        # The caption/text is part of the container creation for all types
        if caption:
            payload["text"] = caption

        try:
            log.info(
                f"Step 1: Creating Threads container for a {payload['media_type']} post..."
            )
            response = requests.post(container_endpoint, params=payload, timeout=90)
            response.raise_for_status()
            creation_id = response.json().get("id")
            if not creation_id:
                log.error(
                    f"Failed to get a creation_id from container response: {response.json()}"
                )
                return False
            log.info(f"Container created successfully. Creation ID: {creation_id}")
        except requests.exceptions.RequestException as e:
            log.error(
                f"Error creating media container: {e.response.text if e.response else e}"
            )
            return False

        # --- 3. Step 2: Publish Media Container ---
        post_id = None
        publish_endpoint = f"{self.base_url}/{self.user_id}/threads_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": self.access_token,
        }
        try:
            log.info(f"Step 2: Publishing container ID: {creation_id}")
            response = requests.post(
                publish_endpoint, params=publish_payload, timeout=60
            )
            response.raise_for_status()
            post_id = response.json().get("id")
            if not post_id:
                log.error(
                    f"Failed to get a post_id from publish response: {response.json()}"
                )
                return False
            log.info(f"🚀 Successfully published to Threads! Post ID: {post_id}")
        except requests.exceptions.RequestException as e:
            log.error(
                f"Error publishing container: {e.response.text if e.response else e}"
            )
            return False

        # --- 4. Post Hashtags as a Reply (if needed) ---
        if post_id and not post_hashtags_in_caption and hashtags:
            formatted_hashtags = self._format_hashtags(hashtags)
            if formatted_hashtags:
                time.sleep(3)  # Give the API a moment to make the post available
                self._post_reply(post_id, formatted_hashtags)

        return True
