# Content Poster

## Prerequirements

- Python 3.x

### Google Sheets 
1. Create new google sheets
2. Add required columns
3. Add sheet and worksheet names into `.env` file.
4. In case column names are wanted to be named differently, rename them and then replace those in `.env` file. 

### Google Cloud Console
1. Go to console.google.com and create new project on account where sheets want to be used on.
2. Go to `API and Services` and add Google Drive API and Google Sheets API
3. Go to credentials page and tap on button `Create new credentials`, then choose Service Account and give it a name and then press create and continue and done.
4. Find this Service Account on `Credentials` page and press on it. Then go to `Keys` and tap on `Add key` and choose `Create new key`, then choose `JSON`. It will download json file, rename it as `credentials.json` and move to project root directory.
5. Get a `client_email` from credentials file and go to sheet that wanted to be used. Tap `Share` and enter this client_email with Editor role.



## Scheduling the Script

To make the script run automatically, you need to set up a scheduled task on your operating system. This will run the `python main.py` command at a regular interval (e.g., every minute).

**Important:** In all examples below, you must replace `/path/to/your/project/` with the **absolute path** to your project's root directory.

  * On Linux and macOS, you can get this path by navigating to your project folder in the terminal and running the `pwd` command.
  * On Windows, you can get it by right-clicking the folder in File Explorer, selecting "Properties", and copying the "Location".
### How to Use It

The user experience is now identical across all operating systems.

To add the scheduled job:

Bash

python setup_scheduler.py add

To remove the scheduled job:

Bash

python setup_scheduler.py remove

Important Note for Windows Users:
To create or delete system-level tasks, you will likely need to run this script from an Administrator Command Prompt or PowerShell. To do this, right-click on the Command Prompt/PowerShell icon and choose "Run as administrator".


## P.S.:
### Scheduling the Script might not work if computer is turned off or entered sleeping mode. To prevent that you have to keep it open and change settings to not stop processes on sleep.
#### Linux
  GUIDE on how to prevent on sleep
#### Windows
  GUIDE on how to prevent on sleep
#### Mac OS
  GUIDE on how to prevent on sleep

