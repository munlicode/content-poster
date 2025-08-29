import os
import time
from typing import Dict, Optional, List
import requests
from interfaces import IDestination
from logger_setup import log
from config import settings
import token_manager
from processors.parse_clean_urls import parse_and_clean_urls
from helpers import upload_to_github


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
        return hashtags

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
            print(response.json())
            post_id = response.json().get("id")
            log.info(f"🚀 Successfully published to Instagram! Post ID: {post_id}")
            return post_id
        except requests.exceptions.RequestException as e:
            log.error(
                f"Error publishing container: {e.response.text if e.response else e}"
            )
            return None

    def post(self, content: Dict) -> bool:
        """Publishes content to Instagram from URLs or local file paths."""
        if not all([self.user_id, self.access_token]):
            return False

        # --- 1. Prepare Content ---
        caption = self._build_caption(
            content.get(settings.TEXT_COLUMN_NAME),
            content.get(settings.HASHTAGS_COLUMN_NAME),
            str(content.get(settings.HASHTAGS_IN_CAPTION_COLUMN_NAME, ""))
            .strip()
            .upper()
            == "TRUE",
        )
        hashtags = content.get(settings.HASHTAGS_COLUMN_NAME)
        # Check the flag. If the column is missing or False, default to posting as a comment.
        # It's only True if the user explicitly sets it to TRUE/true/1 in the sheet.
        post_hashtags_with_text = (
            str(content.get(settings.HASHTAGS_IN_CAPTION_COLUMN_NAME, ""))
            .strip()
            .upper()
            == "TRUE"
        )

        # --- 2. Process Media Sources ---
        image_urls = parse_and_clean_urls(
            content.get(settings.IMAGE_URLS_COLUMN_NAME, "")
        )
        video_urls = parse_and_clean_urls(
            content.get(settings.VIDEO_URLS_COLUMN_NAME, "")
        )
        local_image_path = content.get(
            settings.LOCAL_IMAGE_PATH_COLUMN_NAME, ""
        ).strip()
        local_video_path = content.get(
            settings.LOCAL_VIDEO_PATH_COLUMN_NAME, ""
        ).strip()

        if local_image_path:
            imgur_url = upload_to_github(local_image_path)
            if imgur_url:
                image_urls.append(imgur_url)
            else:
                return False

        all_media_items = [("image", url) for url in image_urls]
        if local_video_path:
            all_media_items.append(("local_video", local_video_path))
        else:
            all_media_items.extend([("video_url", url) for url in video_urls])

        media_count = len(all_media_items)
        if media_count == 0:
            return False

        # --- 3. Create Container(s) ---
        final_container_id = None
        if media_count == 1:
            media_type, media_source = all_media_items[0]
            if media_type == "image":
                final_container_id = self._upload_media_and_get_container_id(
                    media_source, False
                )
            elif media_type == "local_video":
                final_container_id = self._upload_video_from_local_file(
                    media_source, is_carousel_item=False
                )
            elif media_type == "video_url":
                final_container_id = self._upload_video_from_url(
                    media_source, is_carousel_item=False
                )

        elif media_count > 1:
            media_container_ids = []
            for media_type, media_source in all_media_items:
                container_id = None
                if media_type == "image":
                    container_id = self._upload_media_and_get_container_id(
                        media_source, False
                    )
                elif media_type == "local_video":
                    container_id = self._upload_video_from_local_file(
                        media_source, is_carousel_item=True
                    )
                elif media_type == "video_url":
                    container_id = self._upload_video_from_url(
                        media_source, is_carousel_item=True
                    )

                if container_id:
                    media_container_ids.append(container_id)
                else:
                    break

            if len(media_container_ids) == media_count:
                final_container_id = self._create_carousel_container_id(
                    media_container_ids, caption, {}
                )
            else:
                return False

        # --- 4. Publish Final Container ---
        if not final_container_id:
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
        """Polls the container status until it's finished or fails, with improved error logging."""
        # Query for both status_code and the specific error_message field
        fields_to_check = "status_code"

        for _ in range(12):  # Poll for max 60 seconds
            try:
                status_url = f"{self.base_url}/{creation_id}"
                params = {"fields": fields_to_check, "access_token": self.access_token}
                response = requests.get(status_url, params=params)
                response.raise_for_status()
                print(response.json())
                status_data = response.json()
                status = status_data.get("status_code")

                if status == "FINISHED":
                    log.info(f"Container {creation_id} is ready.")
                    return creation_id

                if status == "ERROR":
                    # --- IMPROVEMENT IS HERE ---
                    # Check for a specific error message from the API and log it.
                    error_message = status_data.get(
                        "error_message", "No specific error message provided."
                    )
                    log.error(
                        f"Container {creation_id} failed to process. Reason: {error_message}"
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

    def _upload_video_from_url(
        self, video_url: str, is_carousel_item: bool = False
    ) -> Optional[str]:
        """Uploads a single video from a URL and returns its container ID."""
        endpoint = f"{self.base_url}/{self.user_id}/media"
        params = {"access_token": self.access_token, "video_url": video_url}
        if is_carousel_item:
            params["media_type"] = "VIDEO"
            params["is_carousel_item"] = "true"
        else:
            params["media_type"] = "REELS"

        try:
            log.info(f"Uploading video from URL: {video_url}")
            response = requests.post(endpoint, params=params, timeout=300)
            response.raise_for_status()
            print(response.json())
            creation_id = response.json().get("id")
            return self._check_container_status(creation_id)
        except requests.exceptions.RequestException as e:
            log.error(
                f"Error creating video container from URL: {e.response.text if e.response else e}"
            )
            return None

    def _upload_video_from_local_file(
        self, local_path: str, is_carousel_item: bool = False
    ) -> Optional[str]:
        """Uploads a single video from a local file path and returns its container ID."""
        if not os.path.exists(local_path):
            log.error(f"Local file not found at path: {local_path}")
            return None
        file_size = os.path.getsize(local_path)
        log.info(f"Uploading local video file: {local_path} ({file_size} bytes)")

        endpoint = f"{self.base_url}/{self.user_id}/media"
        params = {"access_token": self.access_token, "upload_type": "resumable"}
        if is_carousel_item:
            params["media_type"] = "VIDEO"
            params["is_carousel_item"] = "true"
        else:
            params["media_type"] = "REELS"

        try:
            response = requests.post(endpoint, params=params)
            response.raise_for_status()
            response_data = response.json()
            container_id, upload_url = response_data.get("id"), response_data.get("uri")
            if not all([container_id, upload_url]):
                return None
        except requests.exceptions.RequestException as e:
            return None

        headers = {
            "Authorization": f"OAuth {self.access_token}",
            "offset": "0",
            "file_size": str(file_size),
        }
        try:
            with open(local_path, "rb") as video_file:
                upload_response = requests.post(
                    upload_url, headers=headers, data=video_file, timeout=600
                )
                upload_response.raise_for_status()
                log.info(
                    f"Successfully uploaded file data for container {container_id}."
                )
        except requests.exceptions.RequestException as e:
            return None
        return self._check_container_status(container_id)

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
            print(response.json())
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
            print(response.json())
            creation_id = response.json().get("id")
            return self._check_container_status(creation_id)
        except requests.exceptions.RequestException as e:
            log.error(f"Error uploading media: {e.response.text if e.response else e}")
            return None
