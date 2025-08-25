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
    git clone https://github.com/munlicode/content-poster
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