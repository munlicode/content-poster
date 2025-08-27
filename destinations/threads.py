from typing import Dict, Optional, List
import requests
from interfaces import IDestination
from logger_setup import log
from config import settings
import token_manager


class ThreadsDestination(IDestination):
    """A destination that posts content to Meta's Threads API."""

    def _build_caption(self, text: Optional[str], hashtags: Optional[str]) -> str:
        """Combines text and hashtags into a single caption string."""
        caption_parts: List[str] = []
        if text:
            caption_parts.append(text)
        if hashtags:
            # Ensure hashtags are space-separated and start with #
            formatted_hashtags = " ".join(
                f"#{tag.strip()}" for tag in hashtags.split(",") if tag.strip()
            )
            caption_parts.append(formatted_hashtags)
        return "\n\n".join(caption_parts)

    def post(self, content: Dict) -> bool:
        """
        Publishes content to Threads. Supports text-only, text with one image,
        or text with one video.
        """
        all_tokens = token_manager.load_token()
        token_data = all_tokens.get("threads", {})

        user_id = token_data.get("user_id")
        access_token = token_data.get("access_token")

        if not all([user_id, access_token]):
            log.error("Missing user_id or access_token. Cannot post to Threads.")
            return False

        # Prepare content from the input dictionary
        text = content.get(settings.TEXT_COLUMN_NAME)
        hashtags = content.get(settings.HASHTAGS_COLUMN_NAME)
        image_urls = content.get(settings.IMAGE_URLS_COLUMN_NAME, "").split(",")
        video_urls = content.get(settings.VIDEO_URLS_COLUMN_NAME, "").split(",")

        # Clean up empty strings from split
        image_url = (
            image_urls[0].strip() if image_urls and image_urls[0].strip() else None
        )
        video_url = (
            video_urls[0].strip() if video_urls and video_urls[0].strip() else None
        )

        caption = self._build_caption(text, hashtags)

        if not caption and not image_url and not video_url:
            log.error("No content (text, image, or video) found to post to Threads.")
            return False

        # --- Build Payload ---
        endpoint = f"{settings.THREADS_API_BASE_URL}{settings.THREADS_API_VERSION}/{user_id}/threads"
        payload = {
            "access_token": access_token,
        }

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

        # --- Create and Publish in one step (New API behavior) ---
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
            return True

        except requests.exceptions.RequestException as e:
            log.error(f"Error posting to Threads: {e}")
            log.error(
                f"Response body: {e.response.text if e.response else 'No response'}"
            )
            return False
