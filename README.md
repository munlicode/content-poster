# Content Poster 🚀

This project automates the process of publishing content to social media platforms like Threads. It fetches scheduled posts from a Google Sheet, intelligently caches them, and publishes them at the specified date and time. It also includes a robust system for automatically refreshing API access tokens and setting up scheduled tasks.

## Features ✨

  * **Google Sheets Integration:** Manage all your content from a simple spreadsheet.
  * **Flexible Scheduling:** Posts are published based on a `date` and `time` column.
  * **Intelligent Caching:** Minimizes API calls by fetching data on a configurable schedule and caching it locally.
  * **Automated Token Refresh:** A separate, daily script ensures your API access token never expires.
  * **Status Tracking:** Automatically updates your Google Sheet with a "Published" or "Failed" status.
  * **Cross-Platform Scheduler:** A helper script automatically sets up the required scheduled tasks on Linux, macOS, and Windows.
  * **Rotating Logs:** Keeps a clean, manageable log file (`app.log`) for easy debugging.

-----

## Setup Guide

Follow these steps to get the project running.

### \#\#\# Step 1: Prerequisites

  * Python 3.8+
  * Git

### \#\#\# Step 2: Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/munlicode/content-poster ("On Windows run from C:/Users/<YOUR_USER_NAME>/")
    cd content-poster
    ```
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

### \#\#\# Step 3: Google Configuration

You'll need to authorize the script to access your Google Sheet.

1.  **Create a Google Sheet:** Set up a sheet with columns for `date`, `text`, `time`, and `status`.
2.  **Create a Google Cloud Project:**
      * Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
      * In your project, go to **APIs & Services** and enable the **Google Drive API** and **Google Sheets API**.
3.  **Create a Service Account:**
      * Go to **Credentials**, click **Create Credentials**, and choose **Service Account**.
      * Give it a name and click **Done**.
4.  **Generate a JSON Key:**
      * Click on your new service account, go to the **Keys** tab, and click **Add Key** \> **Create new key**.
      * Choose **JSON**. A file will be downloaded.
      * Rename this file to `credentials.json` and move it to the root of your project folder.
5.  **Share Your Google Sheet:**
      * Open the `credentials.json` file and copy the `client_email` address.
      * Go to your Google Sheet, click the **Share** button, and share it with that email address, giving it **Editor** permissions.

### \#\#\# Step 4: Application Configuration

The script uses a `.env` file to manage all its settings.

1.  **Create the `.env` file:** Copy the example file to create your own configuration.
    ```bash
    # On Windows (in Command Prompt)
    copy .env.example .env

    # On Linux/macOS
    cp .env.example .env
    ```
2.  **Edit the `.env` file:** Open the new `.env` file and fill in the values for your setup.

-----

## Usage

### \#\#\# Manual Run (for Testing)

You can run the script manually at any time to immediately publish any posts that are due.

```bash
python main.py
```

### \#\#\# Automated Scheduling

A helper script is included to automatically set up the scheduled tasks for both posting and token refreshing.

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

## \#\# Important Note on Scheduling & Sleep Mode

Scheduled tasks can only run if the computer is **on and awake**. If your computer is turned off or in sleep mode, the script will not run.

To ensure continuous operation for a server-like setup, you must configure your power settings to prevent the computer from sleeping automatically.

  * **Windows:**
    1.  Go to **Settings \> System \> Power & Sleep**.
    2.  Set **"When plugged in, PC goes to sleep after"** to **Never**.
  * **macOS:**
    1.  Go to **System Settings \> Displays \> Advanced**.
    2.  Enable **"Prevent automatic sleeping on power adapter when the display is off"**.
    3.  (For older macOS) Go to **System Preferences \> Energy Saver** and check "Prevent computer from sleeping automatically when the display is off".
  * **Linux (Ubuntu/GNOME):**
    1.  Go to **Settings \> Power**.
    2.  Under "Power Saving Options," set **"Screen Blank"** to "Never".
    3.  Ensure **"Automatic Suspend"** is turned off.



# Monitoring Info

app.log

# Troubleshooting
When it fails to run.
Run `schtasks /query /tn "Content Poster Script" /v /fo list` and look on last run time. If it obviously seems not to run, try to move to different directory inside your file system. 

Of course. I will update your `README.md` to include a comprehensive section on how to get and store the Threads API credentials, and how to configure all the application settings using a `.env` file, based on the `Settings` class you provided.

-----

# Content Poster 🚀

This project automates the process of publishing content to social media platforms like Threads. It fetches scheduled posts from a Google Sheet, intelligently caches them, and publishes them at the specified date and time. It also includes a robust system for automatically refreshing API access tokens and setting up scheduled tasks.

## Features ✨

  * **Google Sheets Integration:** Manage all your content from a simple spreadsheet.
  * **Flexible Scheduling:** Posts are published based on a `date` and `time` column.
  * **Intelligent Caching:** Minimizes API calls by fetching data on a configurable schedule (`FETCH_SCHEDULE`).
  * **Automated Token Refresh:** A separate, daily script ensures your API access token never expires.
  * **Status Tracking:** Automatically updates your Google Sheet with a "Published" or "Failed" status.
  * **Cross-Platform Scheduler:** A helper script automatically sets up the required scheduled tasks on Linux, macOS, and Windows.
  * **Centralized Configuration:** All settings are managed in a simple `.env` file.

-----

## Setup Guide

Follow these steps to get the project running.

### \#\#\# Step 1: Prerequisites

  * Python 3.8+
  * Git

### \#\#\# Step 2: Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd content-poster
    ```
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

### \#\#\# Step 3: Google Configuration

Authorize the script to access your Google Sheet.

1.  **Create a Google Sheet:** Set up a sheet with columns for `date`, `text`, `time`, and `status`.
2.  **Create a Google Cloud Project & Service Account:** Follow the detailed steps in the previous README to create a Google Cloud project, enable the **Google Drive & Sheets APIs**, and create a **Service Account**.
3.  **Generate a JSON Key:** Download the service account's JSON key, rename it to `credentials.json`, and place it in the project's root directory.
4.  **Share Your Google Sheet:** Open the `credentials.json` file, copy the `client_email`, and share your Google Sheet with that email address, giving it **Editor** permissions.

### \#\#\# Step 4: Threads API Configuration

Get the necessary credentials to allow the script to post on your behalf. For this single-user application, the **Graph API Explorer** is the most direct method.

1.  **Create a Meta Developer App:**

      * Go to the **[Meta for Developers](https://developers.facebook.com/)** portal, create an account, and create a new **App** of type "Business".
      * In the App Dashboard, add the **"Instagram Graph API"** product and configure it.
      * Ensure your Instagram account is a **Business or Creator Account**.

2.  **Get a Long-Lived Access Token & User ID:**

      * Go to your app's **Tools \> Graph API Explorer**.
      * Generate a **User Access Token** and grant it the `threads_content_publish` permission.
      * The Explorer will show you a short-lived **Access Token** and your **App-Scoped User ID**. Copy the User ID—this is your `INSTAGRAM_USER_ID`.
      * Go to the **[Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/)**, paste the short-lived token, and click **"Extend Access Token"** to get a long-lived token that lasts 60 days. Copy this final token—this is your `THREADS_ACCESS_TOKEN`.

### \#\#\# Step 5: Application Configuration (.env file)

All settings for the application are controlled by a `.env` file.

1.  **Create your `.env` file:** Copy the provided example file.

    ```bash
    # On Windows (in Command Prompt)
    copy .env.example .env

    # On Linux/macOS
    cp .env.example .env
    ```

2.  **Edit your `.env` file:** Open the new `.env` file and fill in all the values you've collected. Below is a description of each setting.

    ```dotenv
    # .env.example

    # --- Threads API Credentials ---
    # Your Instagram Professional Account's unique ID from the Graph API Explorer.
    INSTAGRAM_USER_ID="YOUR_INSTAGRAM_USER_ID"
    # The long-lived (60-day) access token you generated.
    # This will be managed by token_storage.json after the first run.
    THREADS_ACCESS_TOKEN="YOUR_LONG_LIVED_ACCESS_TOKEN"

    # --- Google Sheets Settings ---
    # The name of your Google Sheet document.
    GOOGLE_SHEET_NAME="aaa101"
    # The name of the specific tab within the sheet.
    WORKSHEET_NAME="Sheet1"

    # --- Column Names in Your Google Sheet ---
    # You can change these values if your column headers are different.
    DATE_COLUMN_NAME="date"
    TEXT_COLUMN_NAME="text"
    TIME_COLUMN_NAME="time"
    STATUS_COLUMN_NAME="status"

    # --- Fetch Schedule ---
    # A list of 24-hour "HH:MM" times to fetch new data from Google Sheets.
    # IMPORTANT: Must be a JSON-formatted list (double quotes inside single quotes).
    FETCH_SCHEDULE='["08:00", "13:00", "18:00"]'
    ```

-----

## Usage

### \#\#\# Manual Run (for Testing)

Run the script once to immediately publish any posts that are due.

```bash
python main.py
```

### \#\#\# Automated Scheduling

A helper script automatically sets up the scheduled tasks for both posting and token refreshing.

  * **To add the scheduled jobs:**
    ```bash
    python setup_scheduler.py add
    ```
  * **To remove the scheduled jobs:**
    ```bash
    python setup_scheduler.py remove
    ```

**Note for Windows Users:** You must run these commands from an **Administrator** Command Prompt or PowerShell.















FACEbook
1. create app
2. choose Threads API
3. After app is created to go use cases and press `customize`. In `permissions and features` add threads_basic and threads_content_publish. Then go to `settings` under `permissions and features` and copy threads app id and threads app secret and paste them in .env file. After that a down find `User Token Generator` and press `Add or Remove Threads Testers`. On that page press `Add people` and choose `Threads Testers` and enter usernames that are needed for this test. After invite was sent. Go to `https://threads.com/settings/account` or in app `settings` -> `account` -> `website authorization` -> `invites` and accept invite.
4. Go to `https://developers.facebook.com/tools/explorer/` and press `generate threads access token` then authorize in account that needs to be used and make sure that it is also assigned a role of Threads Tester in step 3. After that in `access token` field get generate Token and run command `python generate_initial_token.py` and paste your token when requested. Then paste user id that is can be collected from access token debugger, where you paste this newly created short-lived token.
