Of course. Here is a complete, updated `README.md` that merges your instructions for both Instagram and Threads, adds the required `APP_ID` and `APP_SECRET`, and abstracts the Google Sheets column names as requested.

-----

# Content Poster 🚀

This project automates publishing content to **Instagram** and **Threads** by fetching scheduled posts from a Google Sheet. It uses intelligent caching to minimize API calls, automatically refreshes API access tokens, and includes helper scripts to set up scheduled tasks across Windows, macOS, and Linux.

-----

## Features ✨

  * **Multi-Platform Support:** Publish to both Instagram (single images/videos, carousels) and Threads.
  * **Google Sheets Integration:** Manage all your content from a simple spreadsheet.
  * **Flexible Scheduling:** Posts are published based on a `date` and `time` in your sheet.
  * **Intelligent Caching:** Minimizes API calls by fetching data only at times you define.
  * **Automated Token Refresh:** A separate, daily script ensures your API access tokens never expire.
  * **Status Tracking:** Automatically updates your Google Sheet with a "Published" or "Failed" status.
  * **Cross-Platform Scheduler:** A helper script automatically sets up the required scheduled tasks.
  * **Centralized Configuration:** All settings are managed in a simple `.env` file.

-----

## Setup Guide

Follow these steps to get the project running.

### Step 1: Prerequisites

  * Python 3.8+
  * Git

### Step 2: Project Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/munlicode/content-poster
    cd content-poster
    ```

    *(**Note for Windows:** It's recommended to clone into your user directory, e.g., `C:/Users/<YOUR_USER_NAME>/`)*

2.  **Create and activate a virtual environment:**

    ```bash
    # Create the venv
    python -m venv venv

    # Activate it (Windows)
    .\venv\Scripts\activate

    # Activate it (Linux/macOS)
    source venv/bin/activate
    ```

3.  **Install the required libraries:**

    ```bash
    pip install -r requirements.txt
    ```

### Step 3: Google Sheets Configuration

1.  **Create a Google Sheet:** Set it up with the necessary columns. The script identifies which data to use based on the column headers you define in your `.env` file. Essential columns are `date`, `time`, and `status`. You can add any others you need, such as `text`, `hashtags`, `image_urls`, `video_urls`, `alt_text`, etc.

2.  **Create a Google Cloud Project & Service Account:**

      * Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
      * In your project, go to **APIs & Services** and enable the **Google Drive API** and **Google Sheets API**.
      * Go to **Credentials**, click **Create Credentials**, and choose **Service Account**. Give it a name and click **Done**.

3.  **Generate a JSON Key:**

      * Click on your new service account, go to the **Keys** tab, and click **Add Key** \> **Create new key**.
      * Choose **JSON**. A file will be downloaded.
      * Rename this file to `credentials.json` and move it to the root of your project folder.

4.  **Share Your Google Sheet:**

      * Open `credentials.json` and copy the `client_email` address.
      * Go to your Google Sheet, click **Share**, and give **Editor** permissions to that email address.

### Step 4: Platform API Configuration

1.  **Create a Meta Developer App:**

      * Go to [Meta for Developers](https://developers.facebook.com/), create an account, and create a new **App** of type "Other" \> "Business".

2.  **Configure the Threads API:**

      * From the App Dashboard, add the **Threads API** product.
      * In the sidebar under **Threads API**, go to **Use Cases** and click **Customize**.
      * Add the `threads_basic` and `threads_content_publish` permissions.
      * Scroll down to **User Token Generator** and add the Threads account you want to post from as a **Tester**.
      * The invited tester must accept the invitation in the Threads app by going to **Settings \> Account \> Website Authorizations \> Invites**.

3.  **Configure the Instagram API:**

      * First, ensure your Instagram account is a **Professional Account (Creator or Business)** and is **linked to a Facebook Page**.
      * From the App Dashboard, add the **Instagram Graph API** product.
      * Go to the **Use Cases** page for the Instagram Graph API and click **Customize** on "API with Facebook Login".
      * Add the following required permissions:
          * `instagram_basic`
          * `instagram_content_publish`
          * `pages_read_engagement`
          * `business_management`
          * `pages_show_list`

### Step 5: Application Configuration (.env)

All application settings are controlled by the `.env` file.

1.  **Create your `.env` file:**

    ```bash
    # On Windows (in Command Prompt)
    copy .env.example .env

    # On Linux/macOS
    cp .env.example .env
    ```

2.  **Edit your `.env` file:** Open the new `.env` file and fill in all the values. The `APP_ID` and `APP_SECRET` are used for generating tokens for both platforms.

    ```dotenv
    # .env

    # --- Meta App Credentials ---
    # Find these in your App Dashboard under Settings > Basic
    APP_ID="YOUR_META_APP_ID"
    APP_SECRET="YOUR_META_APP_SECRET"

    # --- Google Sheets Settings ---
    GOOGLE_SHEET_NAME="Content Schedule"
    WORKSHEET_NAME="Sheet1"

    # --- Column Names in Your Google Sheet ---
    # The script uses these values to find the correct columns.
    # Add or change these to match your sheet's headers.
    DATE_COLUMN_NAME="date"
    TEXT_COLUMN_NAME="text"
    TIME_COLUMN_NAME="time"
    STATUS_COLUMN_NAME="status"
    HASHTAGS_COLUMN_NAME="hashtags"
    IMAGE_URLS_COLUMN_NAME="image_urls"
    VIDEO_URLS_COLUMN_NAME="video_urls"
    POST_ON_INSTAGRAM_COLUMN_NAME="post_on_instagram"
    POST_ON_THREADS_COLUMN_NAME="post_on_threads"

    # --- Fetch Schedule ---
    # A list of 24-hour "HH:MM" times to fetch new data from Google Sheets.
    # IMPORTANT: Must be a JSON-formatted list (double quotes inside single quotes).
    FETCH_SCHEDULE='["08:00", "13:00", "18:00"]'
    ```

### Step 6: Generate and Store Initial Tokens

Now, you will generate the long-lived access tokens for both platforms.

1.  **Get a short-lived Threads token:**

      * Go to your app's **Threads API \> Use Cases** page.
      * Click **Generate Threads Access Token**, select the authorized user, and grant permissions. Copy the generated short-lived token.

2.  **Get a short-lived Instagram token:**

      * Go to **Tools \> Graph API Explorer**.
      * Select your app and choose **"Get User Access Token"**.
      * In the "Permissions" dropdown, select all the Instagram permissions you added in Step 4.
      * Click **Generate Access Token**. Copy the generated short-lived token.

3.  **Run the token generation script:**

    ```bash
    python generate_initial_token.py
    ```

    The script will prompt you for the short-lived token and User ID for **both Instagram and Threads**. Follow the on-screen instructions carefully. You can find the User ID for each token using the [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/).

    The script will automatically generate long-lived tokens and create a `token_storage.json` file to manage your credentials.

-----

## Usage

### Manual Run (for Testing)

You can run the script manually to immediately publish any posts that are due.

```bash
python main.py
```

### Automated Scheduling

A helper script automatically sets up scheduled tasks for posting and token refreshing.

  * **To add the scheduled jobs:**
    ```bash
    python setup_scheduler.py add
    ```
  * **To remove the scheduled jobs:**
    ```bash
    python setup_scheduler.py remove
    ```

**Note for Windows Users:** You must run these commands from an **Administrator** Command Prompt or PowerShell.

-----

## Monitoring and Troubleshooting

  * **Logs:** All actions, successes, and errors are recorded in `app.log`. Check this file first if something goes wrong.
  * **Scheduled Task Issues (Windows):** If you suspect the scheduled task isn't running, open Command Prompt and run:
    ```cmd
    schtasks /query /tn "Content Poster Script" /v /fo list
    ```
    Look at the "Last Run Time" and "Last Result" to diagnose issues.

-----

## Ensuring Continuous Operation: Keep Awake Guide

Scheduled tasks can only run if the computer is **on and awake**. To ensure your content is always posted on time, configure your power settings to prevent the computer from sleeping automatically.

### Windows

1.  Go to **Settings** \> **System** \> **Power & sleep**.
2.  Under "Sleep," set **"When plugged in, PC goes to sleep after"** to **Never**.

### macOS

1.  Go to **System Settings** \> **Displays** \> **Advanced**.
2.  Enable **"Prevent automatic sleeping on power adapter when the display is off"**.

### Linux (Ubuntu/GNOME)

1.  Go to **Settings** \> **Power**.
2.  Under "Power Saving Options," set **"Screen Blank"** to "Never" and ensure **"Automatic Suspend"** is turned off.











NOTES: for threads only first image or video are published.












Of course. A good `README` file is essential for any project. This document will serve as a complete user manual, guiding a new user through the entire process of setting up, configuring, and running the content scheduler.

Here is the complete documentation for your `README.md` file. You can copy and paste this directly into a new `README.md` file in your project's main directory.

-----

# Content Scheduler for Instagram & Threads

This project automates the process of posting content to Instagram and Threads. It reads a schedule and content details from a Google Sheet, sources media from web URLs or your local computer, and posts them at the specified times.

It uses the GitHub API as a temporary host for local media files to generate the public URLs required by the Meta APIs.

## Features

  * **Multi-Platform:** Post to Instagram and/or Threads.
  * **Flexible Scheduling:** Schedule posts for any future date and time.
  * **Versatile Media Sourcing:** Use media from public web URLs or directly from your local computer's file system.
  * **Rich Post Types:** Supports single image/video posts and multi-media carousels.
  * **Hashtag Control:** Automatically post hashtags in the main caption or as a clean first comment on Instagram.
  * **Fully Automated:** Runs on a schedule using cron (Linux/macOS) or Task Scheduler (Windows).
  * **Self-Cleaning:** Includes a utility script to periodically clean up the temporary media files hosted on GitHub.

-----

## Prerequisites

Before you begin, you will need:

  * Python 3.8 or higher.
  * A **Google Account** to create and use a Google Sheet.
  * A **Meta Developer Account** with a configured App.
  * An **Instagram Professional Account** linked to a Facebook Page.
  * A **GitHub Account**.

-----

## ⚙️ Setup Instructions

Follow these steps carefully to set up the entire project.

### 1\. Clone the Repository

First, clone this project to your local machine.

```bash
git clone <your-repository-url>
cd <repository-name>
```

### 2\. Install Dependencies

Create a virtual environment and install the required Python libraries.

```bash
# Create and activate the virtual environment
python -m venv venv
# On Windows:
# venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install libraries from requirements.txt
pip install -r requirements.txt
```

*(You will need to create a `requirements.txt` file containing `requests`, `google-api-python-client`, `google-auth-oauthlib`, `gspread`, and `python-crontab`)*.

### 3\. Set Up Google Sheets API

Your script needs API access to read your Google Sheet.

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project.
3.  Enable the **Google Sheets API** and the **Google Drive API**.
4.  Create credentials for a **Service Account**.
5.  Download the generated JSON key file and rename it to **`credentials.json`**. Place this file in the root directory of your project.
6.  Open the `credentials.json` file, find the `client_email` address, and copy it.
7.  Create your Google Sheet for scheduling, and **share it** with the `client_email` you just copied, giving it "Editor" permissions.

### 4\. Set Up Meta APIs (Instagram & Threads)

1.  Go to [Meta for Developers](https://developers.facebook.com/) and create a new App of type "Business".
2.  From the App Dashboard, add the **"Instagram Graph API"** and **"Threads API"** products.
3.  Use the **Graph API Explorer** tool to generate a long-lived User Access Token. Make sure to grant the following permissions:
      * `instagram_basic`
      * `instagram_content_publish`
      * `pages_read_engagement`
4.  You will need your **Instagram User ID** and the **Threads User ID**. These can be found using the Graph API Explorer.

### 5\. Set Up GitHub API

The script will use a GitHub repository to store your local media files temporarily.

1.  Create a new **Public** GitHub repository. This will be your media storage.
2.  Go to your GitHub **Settings \> Developer settings \> Personal access tokens \> Tokens (classic)**.
3.  Generate a new token with the full **`repo`** scope.
4.  Copy the token immediately and save it.

### 6\. Configure the Script

1.  Rename `config.py.example` to **`config.py`**.
2.  Open `config.py` and fill in all the required values:
      * `GOOGLE_SHEET_NAME`: The exact name of your Google Sheet.
      * `INSTAGRAM_USER_ID`, `INSTAGRAM_ACCESS_TOKEN`, etc.
      * `THREADS_USER_ID`, `THREADS_ACCESS_TOKEN`, etc.
      * `GITHUB_USERNAME`, `GITHUB_REPO_NAME`, `GITHUB_TOKEN`.

### 7\. Schedule the Script

Run the setup script to add the main poster to your system's scheduler. It will run every minute.

```bash
python setup_scheduler.py add
```

-----

## 📝 Usage: The Google Sheet

To schedule a post, add a new row to your Google Sheet and fill in the columns according to the table below.

| Column Name                     | Required? | Description                                                                                                                                                             | Example                                                                          |
| ------------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `Date`                          | **Yes** | The date the post should go live. Format: `YYYY-MM-DD`.                                                                                                                  | `2025-12-25`                                                                     |
| `Time`                          | **Yes** | The time the post should go live (in 24-hour format).                                                                                                                   | `18:30`                                                                          |
| `Status`                        | No        | The script updates this automatically (`Publishing`, `Published`, `Failed`). Leave blank for new posts.                                                                 | `Published`                                                                      |
| `Text`                          | **Yes** | The main caption for your post.                                                                                                                                         | `Hello world!`                                                                   |
| `Image URLs`                    | No        | Comma-separated list of public URLs for images. Used for single posts or carousels.                                                                                     | `https://.../image1.jpg, https://.../image2.jpg`                                   |
| `Video URLs`                    | No        | Comma-separated list of public URLs for videos.                                                                                                                         | `https://.../video1.mp4`                                                         |
| `Local Image Path`              | No        | Comma-separated list of **full local paths** to images on your computer.                                                                                                | `C:\Users\Me\Pictures\photo1.jpg, C:\Users\Me\Pictures\photo2.jpg`               |
| `Local Video Path`              | No        | Comma-separated list of **full local paths** to videos on your computer. Overrides `Video URLs`.                                                                        | `/home/user/videos/clip.mp4`                                                     |
| `Hashtags`                      | No        | Comma-separated list of hashtags.                                                                                                                                       | `#tech, #automation, #python`                                                    |
| `Hashtags with TEXT`            | No        | Set to `TRUE` to include hashtags in the main caption. If `FALSE` or blank, hashtags are posted as a first comment (Instagram only).                                     | `FALSE`                                                                          |
| `Post on Instagram`             | **Yes** | Set to `TRUE` to post to Instagram.                                                                                                                                     | `TRUE`                                                                           |
| `Post on Threads`               | **Yes** | Set to `TRUE` to post to Threads.                                                                                                                                       | `TRUE`                                                                           |
| `Do Not Post Media on Threads`  | No        | Set to `TRUE` to force a text-only post on Threads, even if media is provided.                                                                                           | `TRUE`                                                                           |

-----

## 🧹 Maintenance

The `uploads` folder in your GitHub repository will grow over time. A separate script is provided to clean it out.

To run the cleanup script manually:

```bash
python clean_github_uploads.py
```

It's recommended to schedule this script to run periodically (e.g., once a week).

-----

## ❓ Troubleshooting

  * **`404 Not Found` from GitHub:** Your repository is likely private or your Personal Access Token is missing the `repo` scope.
  * **Video Posts Fail:** Ensure your video file is correctly formatted (MP4, H.264, etc.) and hosted on a public server (like GitHub). Re-encoding with HandBrake's "Web Optimized" setting is recommended.
  * **"Ghost Posts" (Success in logs but not on platform):** This is usually due to Meta's automated content review system. Try posting a different, simpler image and caption to test if your original content was flagged.
  * **`400 Bad Request` from Instagram/Threads:** Double-check that all your media URLs are public and provide a direct link to the file.

