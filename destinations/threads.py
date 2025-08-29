import re
import time
from typing import Dict, Optional, List
import requests
from interfaces import IDestination
from logger_setup import log
from config import settings
import token_manager
from processors.parse_clean_urls import parse_and_clean_urls
from helpers import upload_to_github


class ThreadsDestination(IDestination):
    """A destination that posts content to Meta's Threads API, supporting single and carousel posts from URLs or local files."""

    def __init__(self):
        all_tokens = token_manager.load_token()
        token_data = all_tokens.get("threads", {})
        self.user_id = token_data.get("user_id")
        self.access_token = token_data.get("access_token")
        self.base_url = f"{settings.THREADS_API_BASE_URL}{settings.THREADS_API_VERSION}"

    def _build_caption(
        self, text: Optional[str], hashtags: Optional[str], include_hashtags: bool
    ) -> str:
        caption_parts: List[str] = []
        if text:
            caption_parts.append(text.strip())
        if include_hashtags and hashtags:
            # Simple formatting for Threads hashtags
            formatted_hashtags = " ".join(
                f"#{tag.strip()}"
                for tag in re.split(r"[\s,;]+", hashtags)
                if tag.strip()
            )
            if formatted_hashtags:
                caption_parts.append(formatted_hashtags)
        return "\n\n".join(caption_parts)

    def _post_reply(self, original_post_id: str, reply_text: str) -> bool:
        """Posts a reply to a given Threads post ID using the required two-step process."""
        log.info(f"Attempting to post reply to Thread ID: {original_post_id}")

        # --- Step 1: Create a Reply Container ---
        container_endpoint = f"{self.base_url}/{self.user_id}/threads"
        container_payload = {
            "access_token": self.access_token,
            "media_type": "TEXT",
            "text": reply_text,
            "reply_to_id": original_post_id,
        }
        creation_id = None
        try:
            log.info("Reply Step 1: Creating reply container...")
            response = requests.post(container_endpoint, params=container_payload)
            response.raise_for_status()
            creation_id = response.json().get("id")
            if not creation_id:
                log.error(
                    f"Failed to create reply container. Response: {response.json()}"
                )
                return False
        except requests.exceptions.RequestException as e:
            log.error(
                f"Failed to create reply container. API Error: {e.response.text if e.response else e}"
            )
            return False

        # --- Step 2: Publish the Reply Container ---
        return self._publish_container(creation_id, is_reply=True)

    def _create_item_container(self, media_url: str, is_video: bool) -> Optional[str]:
        """Creates a single container for an item that will go in a carousel."""
        log.info(
            f"Creating carousel item container for {'video' if is_video else 'image'}: {media_url}"
        )
        endpoint = f"{self.base_url}/{self.user_id}/threads"
        params = {"access_token": self.access_token, "is_carousel_item": "true"}
        if is_video:
            params.update({"media_type": "VIDEO", "video_url": media_url})
        else:
            params.update({"media_type": "IMAGE", "image_url": media_url})

        try:
            response = requests.post(endpoint, params=params, timeout=90)
            response.raise_for_status()
            item_id = response.json().get("id")
            if not item_id:
                return None
            log.info(f"Successfully created item container. ID: {item_id}")
            return item_id
        except requests.exceptions.RequestException as e:
            log.error(
                f"Error creating carousel item container: {e.response.text if e.response else e}"
            )
            return None

    def _publish_container(
        self, creation_id: str, is_reply: bool = False
    ) -> Optional[str]:
        """Publishes a finished container (single, carousel, or text) and returns the post ID."""
        log_prefix = "Reply Step 2:" if is_reply else "Publish Step:"
        log.info(f"{log_prefix} Publishing final container ID: {creation_id}")

        time.sleep(3)  # Recommended wait before publishing
        endpoint = f"{self.base_url}/{self.user_id}/threads_publish"
        params = {"creation_id": creation_id, "access_token": self.access_token}
        try:
            response = requests.post(endpoint, params=params, timeout=60)
            response.raise_for_status()
            post_id = response.json().get("id")
            if not post_id:
                log.error(
                    f"Failed to get a post_id from publish response: {response.json()}"
                )
                return None
            log.info(f"🚀 Successfully published! Post ID: {post_id}")
            return post_id
        except requests.exceptions.RequestException as e:
            log.error(
                f"Error publishing container: {e.response.text if e.response else e}"
            )
            return None

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
        caption = self._build_caption(
            text, hashtags, include_hashtags=post_hashtags_in_caption
        )

        # --- 2. Process Media Sources (URLs and Local Files via GitHub) ---
        image_urls = parse_and_clean_urls(
            content.get(settings.IMAGE_URLS_COLUMN_NAME, "")
        )
        video_urls = parse_and_clean_urls(
            content.get(settings.VIDEO_URLS_COLUMN_NAME, "")
        )
        # Handle multiple local image paths
        local_image_paths_raw = content.get(settings.LOCAL_IMAGE_PATH_COLUMN_NAME, "")
        local_image_paths = parse_and_clean_urls(local_image_paths_raw)

        for path in local_image_paths:
            log.info(f"Uploading local image from path: {path}")
            github_url = upload_to_github(path)
            if github_url:
                image_urls.append(github_url)
            else:
                log.error(f"Upload failed for local image: {path}. Halting post.")
                return False  # Stop immediately if any upload fails

        # Handle multiple local video paths
        local_video_paths_raw = content.get(settings.LOCAL_VIDEO_PATH_COLUMN_NAME, "")
        local_video_paths = parse_and_clean_urls(local_video_paths_raw)

        for path in local_video_paths:
            log.info(f"Uploading local video from path: {path}")
            github_url = upload_to_github(path)
            if github_url:
                video_urls.append(github_url)
            else:
                log.error(f"Upload failed for local video: {path}. Halting post.")
                return False  # Stop immediately if any upload fails

        if text_only:
            image_urls, video_urls = [], []

        all_media_urls = image_urls + video_urls
        media_count = len(all_media_urls)

        # --- 3. Create Container(s) based on Media Count ---
        final_container_id = None
        endpoint = f"{self.base_url}/{self.user_id}/threads"

        try:
            if media_count == 0:  # Text-Only Post
                if not caption:
                    log.error("No text found for text-only post.")
                    return False
                log.info("Creating text-only post container...")
                params = {
                    "media_type": "TEXT",
                    "text": caption,
                    "access_token": self.access_token,
                }
                response = requests.post(endpoint, params=params, timeout=90)
                response.raise_for_status()
                final_container_id = response.json().get("id")

            elif media_count == 1:  # Single Media Post
                log.info("Creating single media post container...")
                media_url = all_media_urls[0]
                params = {"text": caption, "access_token": self.access_token}
                if media_url in video_urls:
                    params.update({"media_type": "VIDEO", "video_url": media_url})
                else:
                    params.update({"media_type": "IMAGE", "image_url": media_url})
                response = requests.post(endpoint, params=params, timeout=90)
                response.raise_for_status()
                final_container_id = response.json().get("id")

            elif media_count > 1:  # Carousel Post
                log.info(f"Creating carousel with {media_count} items...")
                child_container_ids = []
                for url in all_media_urls:
                    item_id = self._create_item_container(
                        url, is_video=(url in video_urls)
                    )
                    if item_id:
                        child_container_ids.append(item_id)
                    else:
                        raise ValueError(
                            "Failed to create one or more carousel item containers."
                        )

                log.info("Creating parent carousel container...")
                params = {
                    "media_type": "CAROUSEL",
                    "children": ",".join(child_container_ids),
                    "text": caption,
                    "access_token": self.access_token,
                }
                response = requests.post(endpoint, params=params, timeout=90)
                response.raise_for_status()
                final_container_id = response.json().get("id")

        except (requests.exceptions.RequestException, ValueError) as e:
            log.error(f"Error during container creation phase: {e}")
            return False

        # --- 4. Publish Final Container ---
        if not final_container_id:
            log.error("Failed to create a final container for publishing.")
            return False

        post_id = self._publish_container(final_container_id)
        if post_id and not post_hashtags_in_caption and hashtags:
            reply_hashtags = " ".join(
                f"#{tag.strip()}"
                for tag in re.split(r"[\s,;]+", hashtags)
                if tag.strip()
            )
            if reply_hashtags:
                self._post_reply(post_id, reply_hashtags)

        return post_id is not None
