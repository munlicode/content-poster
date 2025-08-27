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

    def _build_caption(self, text: Optional[str], hashtags: Optional[str]) -> str:
        """Combines text and hashtags into a single caption string."""
        caption_parts: List[str] = []
        if text:
            caption_parts.append(text)
        if hashtags:
            formatted_hashtags = " ".join(
                f"#{tag.strip()}" for tag in hashtags.split(",") if tag.strip()
            )
            caption_parts.append(formatted_hashtags)
        return "\n\n".join(caption_parts)

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

    def _publish_container(self, creation_id: str) -> bool:
        """Publishes a finished container to Instagram."""
        endpoint = f"{self.base_url}/{self.user_id}/media_publish"
        payload = {"creation_id": creation_id, "access_token": self.access_token}
        try:
            log.info(f"Publishing container ID: {creation_id}")
            response = requests.post(endpoint, params=payload)
            response.raise_for_status()
            post_id = response.json().get("id")
            log.info(f"🚀 Successfully published to Instagram! Post ID: {post_id}")
            return True
        except requests.exceptions.RequestException as e:
            log.error(
                f"Error publishing container: {e.response.text if e.response else e}"
            )
            return False

    def post(self, content: Dict) -> bool:
        """Publishes content to Instagram. Supports single image/video or carousels."""
        if not all([self.user_id, self.access_token]):
            log.error("Missing user_id or access_token. Cannot post to Instagram.")
            return False

        # --- 1. Prepare Content ---
        caption = self._build_caption(
            content.get(settings.TEXT_COLUMN_NAME),
            content.get(settings.HASHTAGS_COLUMN_NAME),
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

        # NEW: Extract optional parameters from content dictionary per documentation
        optional_params: Dict[str, Any] = {}
        if content.get("alt_text"):
            optional_params["alt_text"] = content["alt_text"]
        if content.get("location_id"):
            optional_params["location_id"] = content["location_id"]
        if content.get("user_tags"):
            # The API expects a JSON string for user_tags, not a dictionary
            optional_params["user_tags"] = str(content["user_tags"]).replace("'", '"')

        all_media_urls = image_urls + video_urls
        media_count = len(all_media_urls)

        if media_count == 0:
            log.error("Instagram posts require at least one image or video.")
            return False

        # --- 2. Decide Logic Path: Single Media or Carousel ---
        final_container_id = None

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
                # FIX: Use the 'json' argument to send data in the request body, not 'params'
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

        elif media_count > 1:
            log.info("Processing as a carousel post.")
            media_container_ids: List[str] = []

            for url in image_urls:
                container_id = self._upload_media_and_get_container_id(
                    url, is_video=False
                )
                if container_id:
                    media_container_ids.append(container_id)
            for url in video_urls:
                container_id = self._upload_media_and_get_container_id(
                    url, is_video=True
                )
                if container_id:
                    media_container_ids.append(container_id)

            if len(media_container_ids) == media_count:
                final_container_id = self._create_carousel_container_id(
                    media_container_ids, caption, optional_params
                )
            else:
                log.error("Failed to upload one or more media items for the carousel.")
                return False

        # --- 3. Publish the Final Container ---
        if final_container_id:
            return self._publish_container(final_container_id)

        log.error("Could not create a final container for publishing.")
        return False
