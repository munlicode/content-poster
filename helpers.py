import requests
import os
from typing import Optional

from logger_setup import log
from config import settings


def _upload_to_imgur(local_image_path: str) -> Optional[str]:
    """Uploads a local image to Imgur and returns the public URL."""
    if not settings.IMGUR_CLIENT_ID:
        log.error("IMGUR_CLIENT_ID is not set in config. Cannot upload local image.")
        return None
    if not os.path.exists(local_image_path):
        log.error(f"Local image file not found: {local_image_path}")
        return None

    log.info(f"Uploading local image to Imgur: {local_image_path}")
    headers = {"Authorization": f"Client-ID {settings.IMGUR_CLIENT_ID}"}
    try:
        with open(local_image_path, "rb") as image_file:
            response = requests.post(
                "https://api.imgur.com/3/image",
                headers=headers,
                files={"image": image_file},
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            image_url = data.get("data", {}).get("link")
            if image_url:
                log.info(f"Imgur upload successful. Public URL: {image_url}")
                return image_url
            else:
                log.error(f"Imgur API did not return an image link. Response: {data}")
                return None
    except requests.exceptions.RequestException as e:
        log.error(f"Error uploading to Imgur: {e.response.text if e.response else e}")
        return None
