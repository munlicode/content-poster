import requests
from config import settings
from logger_setup import log


def clean_github_uploads_folder():
    """
    Deletes all files from the 'uploads' folder in the configured GitHub repository.
    """
    # --- 1. Load Configuration ---
    if not all(
        [settings.GITHUB_USERNAME, settings.GITHUB_REPO_NAME, settings.GITHUB_TOKEN]
    ):
        log.error(
            "GitHub credentials (username, repo, token) are not fully configured."
        )
        return

    owner = settings.GITHUB_USERNAME
    repo = settings.GITHUB_REPO_NAME
    token = settings.GITHUB_TOKEN
    folder_path = "uploads"
    branch = "main"

    base_api_url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # --- 2. Get the list of files in the 'uploads' folder ---
    contents_url = f"{base_api_url}/contents/{folder_path}"
    try:
        log.info(f"Fetching contents of '{folder_path}' folder...")
        response = requests.get(contents_url, headers=headers)

        # If the folder is not found (e.g., already empty and deleted), it's not an error.
        if response.status_code == 404:
            log.info(
                "The 'uploads' folder does not exist or is empty. Nothing to clean."
            )
            return

        response.raise_for_status()
        files = response.json()

        if not isinstance(files, list) or not files:
            log.info("The 'uploads' folder is empty. Nothing to clean.")
            return

    except requests.exceptions.RequestException as e:
        log.error(
            f"Error fetching folder contents: {e.response.text if e.response else e}"
        )
        return

    # --- 3. Loop through the files and delete each one ---
    log.info(f"Found {len(files)} file(s) to delete.")
    for file_info in files:
        file_path = file_info["path"]
        file_sha = file_info["sha"]
        delete_url = f"{base_api_url}/contents/{file_path}"

        payload = {
            "message": f"Automated cleanup: delete {file_info['name']}",
            "sha": file_sha,
            "branch": branch,
        }

        try:
            log.info(f"Deleting file: {file_path}...")
            del_response = requests.delete(delete_url, headers=headers, json=payload)
            del_response.raise_for_status()
            log.info(f"Successfully deleted {file_path}.")
        except requests.exceptions.RequestException as e:
            log.error(
                f"Failed to delete {file_path}: {e.response.text if e.response else e}"
            )
            # Continue to the next file even if one fails
            continue

    log.info("GitHub uploads folder cleanup complete.")


if __name__ == "__main__":
    clean_github_uploads_folder()
