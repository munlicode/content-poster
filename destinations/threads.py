import time
from typing import Dict, Optional, List
import requests
from interfaces import IDestination
from logger_setup import log
from config import settings
import token_manager


class ThreadsDestination(IDestination):
    """A destination that posts content to Meta's Threads API."""

    # NEW: Helper function to correctly format hashtags.
    def _format_hashtags(self, hashtags: Optional[str]) -> Optional[str]:
        """Formats a comma-separated string of hashtags into a space-separated list."""
        if not hashtags:
            return None

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

    # NEW: Function to post the hashtags as a reply.
    def _post_reply(self, original_post_id: str, reply_text: str) -> bool:
        """Posts a reply to a given Threads post ID."""
        log.info(
            f"Attempting to post hashtags as a reply to Thread ID: {original_post_id}"
        )

        all_tokens = token_manager.load_token()
        token_data = all_tokens.get("threads", {})
        user_id = token_data.get("user_id")
        access_token = token_data.get("access_token")

        endpoint = f"{settings.THREADS_API_BASE_URL}{settings.THREADS_API_VERSION}/{user_id}/threads"
        payload = {
            "access_token": access_token,
            "media_type": "TEXT",
            "text": reply_text,
            "reply_to_id": original_post_id,
        }

        try:
            response = requests.post(endpoint, params=payload)
            response.raise_for_status()
            log.info("✅ Successfully posted hashtags as a reply.")
            return True
        except requests.exceptions.RequestException as e:
            log.error(
                f"Failed to post reply. API Error: {e.response.text if e.response else e}"
            )
            return False

    def post(self, content: Dict) -> bool:
        """Publishes content to Threads and handles hashtags and conditional media."""
        all_tokens = token_manager.load_token()
        token_data = all_tokens.get("threads", {})
        user_id = token_data.get("user_id")
        access_token = token_data.get("access_token")

        if not all([user_id, access_token]):
            log.error("Missing user_id or access_token. Cannot post to Threads.")
            return False

        # --- 1. Prepare Content and Check Flags ---
        text = content.get(settings.TEXT_COLUMN_NAME)
        hashtags = content.get(settings.HASHTAGS_COLUMN_NAME)

        post_hashtags_with_text = content.get(
            settings.HASHTAGS_WITH_TEXT_COLUMN_NAME, ""
        ).strip().lower() in ["true", "1"]
        do_not_post_media = content.get(
            settings.DO_NOT_POST_MEDIA_ON_THREADS_COLUMN_NAME, ""
        ).strip().lower() in ["true", "1"]

        image_urls = content.get(settings.IMAGE_URLS_COLUMN_NAME, "").split(",")
        video_urls = content.get(settings.VIDEO_URLS_COLUMN_NAME, "").split(",")

        image_url = (
            image_urls[0].strip() if image_urls and image_urls[0].strip() else None
        )
        video_url = (
            video_urls[0].strip() if video_urls and video_urls[0].strip() else None
        )

        # If the flag is set, ignore any media URLs
        if do_not_post_media:
            image_url = None
            video_url = None

        caption = self._build_caption(
            text, hashtags, include_hashtags=post_hashtags_with_text
        )

        if not caption and not image_url and not video_url:
            log.error("No content (text, image, or video) found to post to Threads.")
            return False

        # --- 2. Build Payload for the Main Post ---
        endpoint = f"{settings.THREADS_API_BASE_URL}{settings.THREADS_API_VERSION}/{user_id}/threads"
        payload = {"access_token": access_token}

        if image_url:
            payload["media_type"] = "IMAGE"
            payload["image_url"] = image_url
            payload["text"] = caption
        elif video_url:
            payload["media_type"] = "VIDEO"
            payload["video_url"] = video_url
            payload["text"] = caption
        else:
            payload["media_type"] = "TEXT"
            payload["text"] = caption

        # --- 3. Create Main Post and Handle Reply Logic ---
        post_id = None
        try:
            log.info(f"Attempting to post to Threads: '{caption[:50]}...'")
            response = requests.post(endpoint, params=payload, timeout=60)
            response.raise_for_status()
            response_data = response.json()
            post_id = response_data.get("id")

            if not post_id:
                log.error(f"Threads post creation failed. Response: {response_data}")
                return False

            log.info(f"🚀 Successfully published to Threads! Post ID: {post_id}")

        except requests.exceptions.RequestException as e:
            log.error(f"Error posting to Threads: {e}")
            log.error(
                f"Response body: {e.response.text if e.response else 'No response'}"
            )
            return False

        # If the post was successful and we need to post hashtags as a reply
        if post_id and not post_hashtags_with_text and hashtags:
            formatted_hashtags = self._format_hashtags(hashtags)
            if formatted_hashtags:
                time.sleep(3)  # Give the API a moment
                self._post_reply(post_id, formatted_hashtags)

        return post_id is not None
