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