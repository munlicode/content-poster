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
from processors.video_processor import process_and_upload_video


class InstagramDestination(IDestination):
    """A destination that posts content to the Instagram Graph API from URLs or local files."""

    def __init__(self, sheet_name: str, worksheet_name: str):
        all_tokens = token_manager.load_tokens()
        token_data = (
            all_tokens.get(sheet_name, {}).get(worksheet_name, {}).get("instagram", {})
        )
        self.user_id = token_data.get("user_id")
        self.access_token = token_data.get("access_token")
        self.base_url = (
            f"{settings.FACEBOOK_API_BASE_URL}{settings.FACEBOOK_API_VERSION}"
        )

    def _format_hashtags(self, hashtags: Optional[str]) -> Optional[str]:
        """Formats a comma-separated string of hashtags into a space-separated list."""
        if not hashtags:
            return None
        return hashtags
        # --- FIXME: Re-enabled and improved the formatting logic ---
        formatted_tags = []
        for tag in re.split(r"[\s,;]+", hashtags):
            tag = tag.strip()
            if tag:
                if not tag.startswith("#"):
                    formatted_tags.append(f"#{tag}")
                else:
                    formatted_tags.append(tag)
        return " ".join(formatted_tags)

    def _build_caption(
        self, text: Optional[str], hashtags: Optional[str], include_hashtags: bool
    ) -> str:
        caption_parts: List[str] = []
        if text:
            caption_parts.append(text.strip())
        if include_hashtags:
            formatted_hashtags = self._format_hashtags(hashtags)
            if formatted_hashtags:
                caption_parts.append(formatted_hashtags)
        return "\n\n".join(caption_parts)

    def _post_first_comment(self, media_id: str, comment_text: str) -> bool:
        log.info(
            f"Attempting to post hashtags as first comment to media ID: {media_id}"
        )
        endpoint = f"{self.base_url}/{media_id}/comments"
        # --- FIX: Use data=payload for form-encoding, not params and json ---
        payload = {"message": comment_text, "access_token": self.access_token}
        try:
            response = requests.post(endpoint, data=payload)
            response.raise_for_status()
            log.info("✅ Successfully posted hashtags as the first comment.")
            return True
        except requests.exceptions.RequestException as e:
            log.error(
                f"Failed to post first comment. API Error: {e.response.text if e.response else e}"
            )
            return False

    def _publish_container(self, creation_id: str) -> Optional[str]:
        endpoint = f"{self.base_url}/{self.user_id}/media_publish"
        params = {"creation_id": creation_id, "access_token": self.access_token}
        try:
            log.info(f"Publishing container ID: {creation_id}")
            response = requests.post(endpoint, params=params)
            response.raise_for_status()
            post_id = response.json().get("id")
            log.info(f"🚀 Successfully published to Instagram! Post ID: {post_id}")
            return post_id
        except requests.exceptions.RequestException as e:
            log.error(
                f"Error publishing container: {e.response.text if e.response else e}"
            )
            return None

    def _check_container_status(self, creation_id: str) -> Optional[str]:
        fields_to_check = "status_code,status"
        for _ in range(20):
            try:
                status_url = f"{self.base_url}/{creation_id}"
                params = {"fields": fields_to_check, "access_token": self.access_token}
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
                log.error(f"{e}")
                return None
        log.error(f"Container {creation_id} timed out processing.")
        return None

    def _create_carousel_container_id(
        self, media_ids: List[str], caption: str
    ) -> Optional[str]:
        endpoint = f"{self.base_url}/{self.user_id}/media"
        params = {
            "access_token": self.access_token,
            "media_type": "CAROUSEL",
            "children": ",".join(media_ids),
            "caption": caption,
        }
        try:
            log.info(f"Creating carousel container with media IDs: {media_ids}")
            response = requests.post(endpoint, params=params)
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
        """Uploads a single media URL for a carousel and returns its container ID."""
        endpoint = f"{self.base_url}/{self.user_id}/media"
        params = {"access_token": self.access_token, "is_carousel_item": "true"}
        if is_video:
            params["media_type"] = "VIDEO"
            params["video_url"] = media_url
        else:
            params["image_url"] = media_url
        try:
            log.info(
                f"Uploading carousel item ({'video' if is_video else 'image'}) from URL: {media_url}"
            )
            response = requests.post(endpoint, params=params, timeout=300)
            response.raise_for_status()
            creation_id = response.json().get("id")
            return self._check_container_status(creation_id)
        except requests.exceptions.RequestException as e:
            log.error(f"Error uploading media: {e.response.text if e.response else e}")
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

    def post(self, content: Dict) -> bool:
        if not all([self.user_id, self.access_token]):
            return False

        # --- 1. Prepare Content ---
        hashtags = content.get(settings.HASHTAGS_COLUMN_NAME)
        post_hashtags_with_text = (
            str(content.get(settings.HASHTAGS_IN_CAPTION_COLUMN_NAME, ""))
            .strip()
            .upper()
            == "TRUE"
        )
        caption = self._build_caption(
            content.get(settings.TEXT_COLUMN_NAME), hashtags, post_hashtags_with_text
        )

        # --- 2. Process Media Sources ---
        image_urls = parse_and_clean_urls(
            content.get(settings.IMAGE_URLS_COLUMN_NAME, "")
        )
        video_urls = parse_and_clean_urls(
            content.get(settings.VIDEO_URLS_COLUMN_NAME, "")
        )
        local_image_paths = parse_and_clean_urls(
            content.get(settings.LOCAL_IMAGE_PATH_COLUMN_NAME, "")
        )
        local_video_paths = parse_and_clean_urls(
            content.get(settings.LOCAL_VIDEO_PATH_COLUMN_NAME, "")
        )

        for path in local_image_paths:
            github_url = upload_to_github(path)
            if github_url:
                image_urls.append(github_url)
            else:
                return False

        # Build a master list of all media to be processed
        all_media = [("image", url) for url in image_urls]
        if local_video_paths:
            all_media.extend([("local_video", path) for path in local_video_paths])
        else:
            all_media.extend([("video_url", url) for url in video_urls])

        media_count = len(all_media)
        if media_count == 0:
            log.error("Instagram posts require at least one image or video.")
            return False

        # --- 3. Create Container(s) ---
        final_container_id = None
        if media_count == 1:
            log.info("Processing as a single media post.")
            media_type, media_source = all_media[0]

            # --- FIX: Corrected API call for single media posts ---
            all_params = {"access_token": self.access_token, "caption": caption}
            if media_type == "image":
                all_params["image_url"] = media_source
            else:  # Handles both 'local_video' and 'video_url'
                all_params["media_type"] = "REELS"
                if media_type == "local_video":
                    # For local videos, we need to upload to get a URL first
                    public_url = upload_to_github(media_source)
                    if not public_url:
                        return False
                    all_params["video_url"] = public_url
                else:  # video_url
                    all_params["video_url"] = media_source
            try:
                endpoint = f"{self.base_url}/{self.user_id}/media"
                response = requests.post(endpoint, params=all_params, timeout=300)
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
            media_container_ids = []

            for media_type, media_source in all_media:
                container_id = None

                # --- FIX: Correctly determine if the item is a video ---
                is_video = media_type in ["local_video", "video_url"]

                # First, get a public URL for any local files
                public_url = media_source
                if media_type == "local_video":
                    public_url = process_and_upload_video(local_path=public_url)

                # Now upload to Instagram using the public URL
                container_id = self._upload_media_and_get_container_id(
                    public_url, is_video=is_video
                )
                if container_id:
                    media_container_ids.append(container_id)
                else:
                    break

            if len(media_container_ids) == media_count:
                final_container_id = self._create_carousel_container_id(
                    media_container_ids, caption
                )
            else:
                log.error("Failed to upload one or more media items for the carousel.")
                return False

        # --- 4. Publish Final Container ---
        if not final_container_id:
            log.error("Could not create a final container for publishing.")
            return False
        post_id = self._publish_container(final_container_id)
        self.post_id = post_id
        if post_id:
            if not post_hashtags_with_text and hashtags:
                formatted_hashtags = self._format_hashtags(hashtags)
                if formatted_hashtags:
                    time.sleep(3)
                    self._post_first_comment(post_id, formatted_hashtags)
            return True
        return False
