# Content Poster 🚀

This project automates publishing content to Threads by fetching scheduled posts from a Google Sheet. It uses intelligent caching to minimize API calls, automatically refreshes API access tokens, and includes helper scripts to set up scheduled tasks across Windows, macOS, and Linux.

-----

## Features ✨

  * **Google Sheets Integration:** Manage all your content from a simple spreadsheet.
  * **Flexible Scheduling:** Posts are published based on a `date` and `time` in your sheet.
  * **Intelligent Caching:** Minimizes API calls by fetching data only at times you define.
  * **Automated Token Refresh:** A separate, daily script ensures your Threads API access token never expires.
  * **Status Tracking:** Automatically updates your Google Sheet with a "Published" or "Failed" status.
  * **Cross-Platform Scheduler:** A helper script automatically sets up the required scheduled tasks.
  * **Centralized Configuration:** All settings are managed in a simple `.env` file.

-----

## Setup Guide

Follow these steps to get the project running.

### \#\#\# Step 1: Prerequisites

  * Python 3.8+
  * Git

### \#\#\# Step 2: Project Installation

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

### \#\#\# Step 3: Google Configuration

Authorize the script to access your Google Sheet.

1.  **Create a Google Sheet:** Set it up with columns for `date`, `text`, `time`, and `status`.
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

### \#\#\# Step 4: Threads API Configuration

Follow these steps carefully to get the necessary API credentials.

1.  **Create a Meta Developer App:**

      * Go to [Meta for Developers](https://developers.facebook.com/), create an account, and create a new **App** of type "Other" \> "Business".
      * From the App Dashboard, add the **Threads API** product.

2.  **Configure Permissions and Testers:**

      * In the sidebar under **Threads API**, go to **Use Cases**.
      * Click **Customize**.
      * Add the `threads_basic` and `threads_content_publish` permissions.
      * Scroll down to **User Token Generator** and click **Add or Remove Threads Testers**. Add the Threads accounts you want to post from.
      * The invited users must accept the invitation by going to **Threads \> Settings \> Account \> Website Authorizations \> Invites**.

3.  **Generate Your Initial Tokens:**

      * Go back to your app's **Use Cases** page and find the **User Token Generator** section again.
      * Click **Generate Threads Access Token**. Select the user you authorized and grant the permissions.
      * A short-lived Access Token will be generated. **Copy this token.**
      * Open the [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/), paste the short-lived token, and click "Debug".
      * Copy the **User ID** shown in the debugger results. You will need both the token and User ID for the next step.

4.  **Store Credentials Securely:**

      * Run the included `generate_initial_token.py` script:
        ```bash
        python generate_initial_token.py
        ```
      * When prompted, paste the **short-lived Access Token** and the **User ID** you collected in the previous step.
      * The script will automatically generate a long-lived token and create a `token_storage.json` file. This file will manage your credentials and refresh them automatically.

### \#\#\# Step 5: Application Configuration (.env)

All settings for the application are controlled by a `.env` file.

1.  **Create your `.env` file:**

    ```bash
    # On Windows (in Command Prompt)
    copy .env.example .env

    # On Linux/macOS
    cp .env.example .env
    ```

2.  **Edit your `.env` file:** Open the new `.env` file and fill in all the values.

    ```dotenv
    # .env

    # --- Google Sheets Settings ---
    # The name of your Google Sheet document.
    GOOGLE_SHEET_NAME="Content Schedule"
    # The name of the specific tab within the sheet.
    WORKSHEET_NAME="Sheet1"

    # --- Column Names in Your Google Sheet ---
    # You can change these if your column headers are different.
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

You can run the script manually to immediately publish any posts that are due.

```bash
python main.py
```

### \#\#\# Automated Scheduling

A helper script is included to automatically set up scheduled tasks for both posting and token refreshing.

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
    Look at the "Last Run Time" and "Last Result" to diagnose issues. If it fails to run, try moving the project to a different directory.

-----

## Ensuring Continuous Operation: Keep Awake Guide  कंप्यूटर

Scheduled tasks can only run if the computer is **on and awake**. If your computer is turned off or in sleep mode, the script will not run. To ensure your content is always posted on time, you must configure your power settings to prevent the computer from sleeping automatically.

### Windows

1.  Go to **Settings** \> **System** \> **Power & sleep**.
2.  Under "Sleep," set **"When plugged in, PC goes to sleep after"** to **Never**.

### macOS

1.  Go to **System Settings** \> **Displays** \> **Advanced**.
2.  Enable **"Prevent automatic sleeping on power adapter when the display is off"**.
3.  *(For older macOS versions)* Go to **System Preferences** \> **Energy Saver** and check "Prevent computer from sleeping automatically when the display is off".

### Linux (Ubuntu/GNOME)

1.  Go to **Settings** \> **Power**.
2.  Under "Power Saving Options," set **"Screen Blank"** to "Never".
3.  Ensure **"Automatic Suspend"** is turned off.