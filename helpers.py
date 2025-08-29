import requests
import os
from typing import Optional
import uuid
import base64


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


def _upload_to_imgbb(local_image_path: str) -> Optional[str]:
    """Uploads a local image to ImgBB and returns the public URL."""
    if not settings.IMGBB_API_KEY:
        log.error("IMGBB_API_KEY is not set in config.")
        return None
    if not os.path.exists(local_image_path):
        log.error(f"Local image file not found: {local_image_path}")
        return None

    log.info(f"Uploading local image to ImgBB: {local_image_path}")
    url = "https://api.imgbb.com/1/upload"
    payload = {"key": settings.IMGBB_API_KEY}

    try:
        with open(local_image_path, "rb") as image_file:
            response = requests.post(
                url, params=payload, files={"image": image_file}, timeout=120
            )
            response.raise_for_status()
            data = response.json()
            # The direct URL is in data -> data -> url
            image_url = data.get("data", {}).get("url")
            if image_url:
                log.info(f"ImgBB upload successful. Public URL: {image_url}")
                return image_url
            else:
                log.error(f"ImgBB API did not return an image link. Response: {data}")
                return None
    except requests.exceptions.RequestException as e:
        log.error(f"Error uploading to ImgBB: {e.response.text if e.response else e}")
        return None


def upload_to_github(local_file_path: str) -> Optional[str]:
    """
    Uploads a local file to a specified GitHub repository using the Contents API
    and returns the raw public URL. This is a simple, one-step process.
    """
    if not all(
        [settings.GITHUB_USERNAME, settings.GITHUB_REPO_NAME, settings.GITHUB_TOKEN]
    ):
        log.error(
            "GitHub credentials (username, repo, token) are not fully configured."
        )
        return None

    if not os.path.exists(local_file_path):
        log.error(f"Local file not found at path: {local_file_path}")
        return None

    # --- Prepare File and API Details ---
    owner = settings.GITHUB_USERNAME
    repo = settings.GITHUB_REPO_NAME
    token = settings.GITHUB_TOKEN
    branch = "main"

    file_extension = os.path.splitext(local_file_path)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    repo_file_path = f"uploads/{unique_filename}"

    endpoint = f"https://api.github.com/repos/{owner}/{repo}/contents/{repo_file_path}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        # --- Read and Base64 encode the file content ---
        with open(local_file_path, "rb") as f:
            content = f.read()
        encoded_content = base64.b64encode(content).decode("utf-8")

        # --- Create the API payload ---
        payload = {
            "message": f"Automated upload: {unique_filename}",
            "content": encoded_content,
            "branch": branch,
        }

        # --- Make the API call ---
        log.info(f"Uploading file to GitHub: {repo_file_path}")
        # Use PUT to create a new file
        response = requests.put(endpoint, headers=headers, json=payload, timeout=120)
        response.raise_for_status()

        # The response contains the URL we need
        response_data = response.json()
        download_url = response_data.get("content", {}).get("download_url")

        if download_url:
            log.info(f"GitHub upload successful. Public URL: {download_url}")
            return download_url
        else:
            log.error(
                f"Could not find 'download_url' in GitHub API response: {response_data}"
            )
            return None

    except requests.exceptions.RequestException as e:
        log.error(
            f"Error during GitHub API call: {e.response.text if e.response else e}"
        )
        return None
