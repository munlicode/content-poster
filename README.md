# Content Scheduler for Instagram & Threads 🚀

This project automates publishing content to **Instagram** and **Threads** directly from a Google Sheet. It handles scheduling, media uploads from local files or URLs, and API token management, allowing you to build a complete, hands-off content pipeline.

-----

## ✨ Features

  * **Multi-Platform:** Publish to Instagram (single images/videos, carousels) and Threads (single images/videos, text).
  * **Google Sheets Backend:** Manage your entire content schedule from a single, simple spreadsheet.
  * **Flexible Media Sourcing:** Use media from public web URLs or upload directly from your local computer.
  * **Automated Token Management:** A daily script automatically refreshes API access tokens to ensure uninterrupted operation.
  * **Status Tracking:** Automatically updates your Google Sheet with a `Published` or `Failed` status for each post.
  * **Cross-Platform Scheduler:** A helper script automatically sets up the required scheduled tasks on Windows, macOS, and Linux.
  * **Local File Hosting:** Automatically uploads local media to a designated GitHub repository to generate the public URLs required by the Meta APIs.

-----

## ⚙️ Setup Guide

Follow these steps carefully to configure and launch the scheduler.

### 1\. Prerequisites

  * Python 3.8+
  * Git
  * A Google Account
  * A Meta Developer Account
  * An Instagram Professional Account linked to a Facebook Page
  * A GitHub Account

### 2\. Project Installation

1.  **Clone the repository:**

    ```bash
    git clone htts://github.com/munlicode/content-poster
    cd content-poster
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    # Create the venv
    python -m venv venv

    # Activate it (Windows)
    .\venv\Scripts\activate

    # Activate it (macOS/Linux)
    source venv/bin/activate
    ```

3.  **Install the required libraries:**

    ```bash
    pip install -r requirements.txt
    ```

### 3\. Google Sheets API

1.  **Create a Google Sheet** with the columns you need (see the Usage section for details).
2.  Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
3.  In your project, enable the **Google Drive API** and **Google Sheets API**.
4.  Go to **Credentials**, click **Create Credentials**, and choose **Service Account**.
5.  On the Keys tab for your new service account, create a **JSON** key. A `credentials.json` file will be downloaded. Move this file to the root of your project folder.
6.  Open `credentials.json`, copy the `client_email` address, and **Share** your Google Sheet(s) with that email, granting it **Editor** permissions.

### 4\. Meta APIs (Instagram & Threads)

1.  Go to [Meta for Developers](https://developers.facebook.com/) and create a new App of type "Business" with Use Cases Instragram and Threads
2.  Go to Use Cases in app dashboard
3.  For the **Instagram API**, grant at least the following permissions in the App's settings:
      * `instagram_basic`
      * `instagram_content_publish`
      * `pages_read_engagement`
      * `business_management`
      * `pages_show_list`
4.  For the **Threads API**, grant `threads_basic` and `threads_content_publish` permissions.
5. Go to `App Roles` -> `Roles` and add `threads testing account` that you want to use. After that go to threads mobile app `Settings` -> `Account` -> `Website-Authorization` -> `Invites` and accept request from your app
6. Go to [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/)
7. First on facebook domain give permissions for instagram account that access token needs and then click `Generate Access Token` and authorize your account. After you get this access token, go to [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/) and apply debug for your new access token. From shown data under `Granular Scopes` get numerical id near `instagram_basic` and save it somewhere. It is your instagram account id.
8. Now do the same process for threads account. In order to do so, instead of facebook choose threads.net in domain and go through the same process
  

### 5\. GitHub API for Media Hosting

1.  Create a new **Public** GitHub repository. This will be used to store your media files.
2.  Go to your GitHub **Settings \> Developer settings \> Personal access tokens \> Tokens (classic)**.
3.  Generate a new token with the full **`repo`** scope. Copy the token immediately.

### 6\. Application Configuration (.env)

1.  Create your `.env` file from the example template:

    ```bash
    # On Windows
    copy .env.example .env

    # On macOS/Linux
    cp .env.example .env
    ```

2.  Open the new `.env` file and fill in all the values. The script uses the `*_COLUMN_NAME` variables to find the correct columns in your sheet, regardless of their order.

### 7\. Generate API Tokens
1.   Run the token generation script. It will prompt you for action type, sheet name, workspace name, the short-lived token and User ID for both Instagram and Threads.

```bash
  python generate_initial_token.py
```

This will create a `token_storage.json` file with permanent, auto-refreshing tokens.

-----

## 📝 Usage

### The Google Sheet

To schedule a post, add a new row and fill in the columns.

| Column Name                    | Required? | Description                                                                                         | Example                                          |
| ------------------------------ | :-------: | --------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `Date`                         |  **Yes**  | Post date in `YYYY-MM-DD` format.                                                                   | `2025-12-25`                                     |
| `Time`                         |  **Yes**  | Post time in 24-hour `HH:MM` format.                                                                | `18:30`                                          |
| `Status`                       |    No     | Leave blank. The script updates this to `Published` or `Failed`.                                    | `Published`                                      |
| `Text`                         |  **Yes**  | The main caption for your post.                                                                     | `Check out this amazing view!`                   |
| `Image URLs`                   |    No     | Comma-separated public URLs for images.                                                             | `https://.../image1.jpg, https://.../image2.jpg` |
| `Video URLs`                   |    No     | Comma-separated public URLs for videos.                                                             | `https://.../video1.mp4`                         |
| `Local Image Path`             |    No     | Comma-separated full local paths to images.                                                         | `C:\Users\Me\Pictures\photo1.jpg`                |
| `Local Video Path`             |    No     | Comma-separated full local paths to videos. Overrides `Video URLs`.                                 | `/home/user/videos/clip.mp4`                     |
| `Hashtags`                     |    No     | Comma-separated hashtags.                                                                           | `#travel, #scenery, #automation`                 |
| `Hashtags with TEXT`           |    No     | `TRUE` to add hashtags to the caption. Blank or `FALSE` for a first comment on Instagram.           | `FALSE`                                          |
| `Post on Instagram`            |  **Yes**  | `TRUE` to post to Instagram.                                                                        | `TRUE`                                           |
| `Post on Threads`              |  **Yes**  | `TRUE` to post to Threads.                                                                          | `TRUE`                                           |
| `Do Not Post Media on Threads` |    No     | `TRUE` to force a text-only post on Threads. *Note: Threads only supports one media item per post.* | `FALSE`                                          |

### Running the Script

  * **Manual Run (for testing):**

    ```bash
    python main.py
    ```

  * **Automated Scheduling:** Use the helper script to manage scheduled tasks. **Note:** On Windows, you must run this from an **Administrator** terminal.

    ```bash
    # Add all jobs (poster, token refresh, repo cleanup)
    python setup_scheduler.py add

    # Remove all jobs
    python setup_scheduler.py remove
    ```

-----
### Additional
  * **Fill Google Sheets:** You might want script to fill your google sheets automatically, so you can run `python setup_google_sheet.py` to do so. 
    * Please note that script might fail if locale is not compatable with English. In this case you need to change locale of google sheet to english or so.
  * **Update Script Execution Frequency:** If you want script to run not by default frequency, you can set `MAIN_SCRIPT_RUN_FREQUENCY_MINUTES` in .env file to some positive integer like `5`. It will make script to run every 5 minutes instead.
-----

## 🧹 Maintenance

The `uploads` folder in your GitHub repository will fill up with media over time. A script is included to clean this folder.

```bash
python clean_github_uploads.py
```

This script is also scheduled to run weekly when you use `setup_scheduler.py add`.

-----

## ❓ Troubleshooting

  * **`404 Not Found` from GitHub:** Your repository is private, or your Personal Access Token is missing the full `repo` scope.
  * **Video Posts Fail on Instagram/Threads:** Your video file is likely not formatted correctly. Re-encode it using a tool like [HandBrake](https://handbrake.fr/) with the **"Web Optimized"** setting checked.
  * **"Ghost Posts" (Success in logs but not visible):** This is often caused by Meta's automated content review. Test with a different, simpler image and caption to see if your original content was flagged.
  * **`400 Bad Request`:** Check that all your media URLs are public and provide a direct link to the file, not a webpage.
