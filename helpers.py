import requests
import os
from typing import Optional
import uuid
import base64

from logger_setup import log
from config import settings
from token_manager import load_tokens


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


def get_workspace_names():
    tokens = load_tokens()
    return tokens.keys()
