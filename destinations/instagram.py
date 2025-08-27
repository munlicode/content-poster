import time
from typing import Dict, Optional, List, Any
import requests
from interfaces import IDestination
from logger_setup import log
from config import settings
import token_manager


class InstagramDestination(IDestination):
    """A destination that posts content to the Instagram Graph API."""

    def __init__(self):
        all_tokens = token_manager.load_token()
        token_data = all_tokens.get("instagram", {})

        self.user_id = token_data.get("user_id")
        self.access_token = token_data.get("access_token")
        self.base_url = (
            f"{settings.FACEBOOK_API_BASE_URL}{settings.FACEBOOK_API_VERSION}"
        )

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

    # MODIFIED: This function now only handles the main text for the caption.
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

    # NEW: Function to post the hashtags as the first comment.
    def _post_first_comment(self, media_id: str, comment_text: str) -> bool:
        """Posts a comment to a given media ID."""
        log.info(
            f"Attempting to post hashtags as first comment to media ID: {media_id}"
        )
        endpoint = f"{self.base_url}/{media_id}/comments"
        params = {"access_token": self.access_token}
        payload = {"message": comment_text}

        try:
            response = requests.post(endpoint, params=params, json=payload)
            response.raise_for_status()
            log.info("✅ Successfully posted hashtags as the first comment.")
            return True
        except requests.exceptions.RequestException as e:
            log.error(
                f"Failed to post first comment. API Error: {e.response.text if e.response else e}"
            )
            return False

    # MODIFIED: Now returns the post_id on success, or None on failure.
    def _publish_container(self, creation_id: str) -> Optional[str]:
        """Publishes a finished container to Instagram and returns the media ID."""
        endpoint = f"{self.base_url}/{self.user_id}/media_publish"
        payload = {"creation_id": creation_id, "access_token": self.access_token}
        try:
            log.info(f"Publishing container ID: {creation_id}")
            response = requests.post(endpoint, params=payload)
            response.raise_for_status()
            post_id = response.json().get("id")
            log.info(f"🚀 Successfully published to Instagram! Post ID: {post_id}")
            return post_id
        except requests.exceptions.RequestException as e:
            log.error(
                f"Error publishing container: {e.response.text if e.response else e}"
            )
            return None

    def post(self, content: Dict) -> bool:
        """Publishes content to Instagram and handles hashtags as a first comment."""
        if not all([self.user_id, self.access_token]):
            log.error("Missing user_id or access_token. Cannot post to Instagram.")
            return False

        # --- 1. Prepare Content ---
        text = content.get(settings.TEXT_COLUMN_NAME)
        hashtags = content.get(settings.HASHTAGS_COLUMN_NAME)
        # Check the flag. If the column is missing or False, default to posting as a comment.
        # It's only True if the user explicitly sets it to TRUE/true/1 in the sheet.
        post_hashtags_with_text = content.get(
            settings.HASHTAGS_WITH_TEXT_COLUMN_NAME, ""
        ).strip().lower() in ["true", "t", "1"]

        caption = self._build_caption(
            text, hashtags, include_hashtags=post_hashtags_with_text
        )

        image_urls = [
            url.strip()
            for url in content.get(settings.IMAGE_URLS_COLUMN_NAME, "").split(",")
            if url.strip()
        ]
        video_urls = [
            url.strip()
            for url in content.get(settings.VIDEO_URLS_COLUMN_NAME, "").split(",")
            if url.strip()
        ]
        optional_params: Dict[str, Any] = {}  # etc.

        all_media_urls = image_urls + video_urls
        media_count = len(all_media_urls)
        log.info(f"Media Count: {media_count}")
        if media_count == 0:
            log.error("Instagram posts require at least one image or video.")
            return False

        # --- 2. Create Media Container ---
        final_container_id = None
        # (The entire 'if media_count == 1:' and 'elif media_count > 1:' logic remains the same)
        if media_count == 1:
            log.info("Processing as a single media post.")
            single_media_url = all_media_urls[0]
            is_video = single_media_url in video_urls

            endpoint = f"{self.base_url}/{self.user_id}/media"
            params = {"access_token": self.access_token}
            payload = {
                "caption": caption,
                "media_type": "VIDEO" if is_video else "IMAGE",
                **optional_params,
            }

            if is_video:
                payload["video_url"] = single_media_url
            else:
                payload["image_url"] = single_media_url

            try:
                response = requests.post(
                    endpoint, params=params, json=payload, timeout=300
                )
                response.raise_for_status()
                final_container_id = self._check_container_status(
                    response.json().get("id")
                )
            except requests.exceptions.RequestException as e:
                log.error(
                    f"Error creating single media container: {e.response.text if e.response else e}"
                )
                return False

        # --- 3. Publish and Post First Comment ---
        if not final_container_id:
            log.error("Could not create a final container for publishing.")
            return False

        # Publish the container and get the post_id
        post_id = self._publish_container(final_container_id)

        if post_id:
            # If the post was successful AND we are supposed to post hashtags as a comment...
            if not post_hashtags_with_text and hashtags:
                formatted_hashtags = self._format_hashtags(hashtags)
                if formatted_hashtags:
                    # Give the API a moment before posting the comment
                    time.sleep(3)
                    self._post_first_comment(post_id, formatted_hashtags)
            return True  # The main post was successful

        return False  # The main post failed

    def _check_container_status(self, creation_id: str) -> Optional[str]:
        """Polls the container status until it's finished or fails."""
        for _ in range(12):  # Poll for max 60 seconds
            try:
                status_url = f"{self.base_url}/{creation_id}"
                params = {"fields": "status_code", "access_token": self.access_token}
                response = requests.get(status_url, params=params)
                response.raise_for_status()
                status_data = response.json()
                status = status_data.get("status_code")

                if status == "FINISHED":
                    log.info(f"Container {creation_id} is ready.")
                    return creation_id
                if status == "ERROR":
                    log.error(
                        f"Container {creation_id} failed to process. Details: {status_data}"
                    )
                    return None

                log.info(f"Container {creation_id} status is '{status}'. Waiting...")
                time.sleep(5)
            except requests.exceptions.RequestException as e:
                log.error(
                    f"Error checking container status: {e.response.text if e.response else e}"
                )
                return None
        log.error(f"Container {creation_id} timed out processing.")
        return None

    def _create_carousel_container_id(
        self, media_ids: List[str], caption: str, optional_params: Dict
    ) -> Optional[str]:
        """Creates a carousel container from multiple media container IDs."""
        endpoint = f"{self.base_url}/{self.user_id}/media"
        payload = {
            "access_token": self.access_token,
            "media_type": "CAROUSEL",
            "children": ",".join(media_ids),
            "caption": caption,
            **optional_params,  # NEW: Add optional params like location_id
        }
        try:
            log.info(f"Creating carousel container with media IDs: {media_ids}")
            response = requests.post(endpoint, params=payload)
            response.raise_for_status()
            creation_id = response.json().get("id")
            return self._check_container_status(creation_id)
        except requests.exceptions.RequestException as e:
            log.error(
                f"Error creating carousel container: {e.response.text if e.response else e}"
            )
            return None

    def _upload_media_and_get_container_id(
        self, media_url: str, is_video: bool
    ) -> Optional[str]:
        """Uploads a single media file for a carousel and returns its container ID."""
        endpoint = f"{self.base_url}/{self.user_id}/media"
        payload = {
            "access_token": self.access_token,
            "media_type": "VIDEO" if is_video else "IMAGE",
            "is_carousel_item": "true",
        }
        if is_video:
            payload["video_url"] = media_url
        else:
            payload["image_url"] = media_url
            payload.pop("media_type")

        try:
            log.info(
                f"Uploading carousel item ({'video' if is_video else 'image'}) from URL: {media_url}"
            )
            response = requests.post(endpoint, params=payload, timeout=300)
            response.raise_for_status()
            creation_id = response.json().get("id")
            return self._check_container_status(creation_id)
        except requests.exceptions.RequestException as e:
            log.error(f"Error uploading media: {e.response.text if e.response else e}")
            return None
