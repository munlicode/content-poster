import os
import sys
import subprocess

# --- Configuration ---
# Names for the main posting job
JOB_COMMENT = "Content Poster Job"  # Used for Linux/macOS cron
TASK_NAME = "Content Poster Script"  # Used for Windows Task Scheduler

# Names for the token refresh job
REFRESH_JOB_COMMENT = "Content Poster Token Refresh Job"
REFRESH_TASK_NAME = "Content Poster Token Refresh Script"


def get_paths():
    """
    Determines the absolute paths for the project and Python interpreter,
    handling differences between Windows and Unix-like systems.
    """
    project_path = os.path.dirname(os.path.abspath(__file__))

    if sys.platform.startswith("win"):
        # Windows path for the Python interpreter in a venv
        python_path = os.path.join(project_path, "venv", "Scripts", "python.exe")
    else:
        # Linux/macOS path
        python_path = os.path.join(project_path, "venv", "bin", "python")

    main_script_path = os.path.join(project_path, "main.py")
    refresh_script_path = os.path.join(project_path, "refresh_token.py")

    return project_path, python_path, main_script_path, refresh_script_path


# --- Windows Functions ---
def setup_windows_task():
    """Creates or updates a task in Windows Task Scheduler."""
    project_path, python_path, main_script_path, refresh_script_path = get_paths()

    print(f"Setting up Windows Tasks: {TASK_NAME} & {REFRESH_TASK_NAME}")

    # The command that Task Scheduler will run
    # --- 1. Setup for Main Posting Task (every minute) ---
    main_command = f'"{python_path}" "{main_script_path}"'

    # schtasks command to create a new task that runs every minute
    # /SC MINUTE /MO 1: Sets the schedule
    # /TN: Sets the Task Name
    # /TR: Sets the Task Run command (what to execute)
    # /RU SYSTEM: Runs the task as the SYSTEM user, so it runs even if you're not logged in
    # /F: Forces the creation and overwrites the task if it already exists
    schtasks_main_command = [
        "schtasks",
        "/create",
        "/SC",
        "MINUTE",
        "/MO",
        "1",
        "/TN",
        TASK_NAME,
        "/TR",
        f'cmd /c "cd /d {project_path} && {main_command}"',
        "/RU",
        "SYSTEM",
        "/F",
    ]

    # --- 2. Setup for Token Refresh Task (daily at 3 AM) ---
    refresh_command = f'"{python_path}" "{refresh_script_path}"'
    schtasks_refresh_command = [
        "schtasks",
        "/create",
        "/SC",
        "DAILY",
        "/ST",
        "03:00",
        "/TN",
        REFRESH_TASK_NAME,
        "/TR",
        f'cmd /c "cd /d {project_path} && {refresh_command}"',
        "/RU",
        "SYSTEM",
        "/F",
    ]

    try:
        print(f"Setting up Windows Task: {TASK_NAME}")
        subprocess.run(
            schtasks_main_command, check=True, capture_output=True, text=True
        )
        print(f"Setting up Windows Task: {REFRESH_TASK_NAME}")
        subprocess.run(
            schtasks_refresh_command, check=True, capture_output=True, text=True
        )
        print("\nSuccess! Both scheduler tasks have been set up.")
    except subprocess.CalledProcessError as e:
        print(
            f"ERROR: Could not create a task. You may need to run this script as an Administrator."
        )
        print(f"Details: {e.stderr}")


def remove_windows_task():
    """Deletes both tasks from Windows Task Scheduler."""
    commands_to_run = [
        ["schtasks", "/delete", "/TN", TASK_NAME, "/F"],
        ["schtasks", "/delete", "/TN", REFRESH_TASK_NAME, "/F"],
    ]

    print("Removing scheduler tasks...")
    for command in commands_to_run:
        task_name_to_remove = command[3]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"- Task '{task_name_to_remove}' removed successfully.")
        except subprocess.CalledProcessError as e:
            if "ERROR: The specified task name" in e.stderr:
                print(f"- Task '{task_name_to_remove}' not found. Nothing to remove.")
            else:
                print(
                    f"ERROR removing task '{task_name_to_remove}'. You may need Admin rights."
                )
                print(f"Details: {e.stderr}")


# --- Linux & macOS Functions ---
def setup_unix_job():
    """Adds or updates both cron jobs for Linux/macOS."""
    from crontab import CronTab

    project_path, python_path, main_script_path, refresh_script_path = get_paths()

    main_command = f"cd {project_path} && {python_path} {main_script_path}"
    refresh_command = f"cd {project_path} && {python_path} {refresh_script_path}"

    cron = CronTab(user=True)
    # Remove old jobs to avoid duplicates
    cron.remove_all(comment=JOB_COMMENT)
    cron.remove_all(comment=REFRESH_JOB_COMMENT)

    # Create main job (every minute)
    main_job = cron.new(command=main_command, comment=JOB_COMMENT)
    main_job.minute.every(1)

    # Create refresh job (daily at 3 AM)
    refresh_job = cron.new(command=refresh_command, comment=REFRESH_JOB_COMMENT)
    refresh_job.setall("0 3 * * *")

    cron.write()
    print("Success! Both cron jobs have been set up.")
    print("To see them, run: crontab -l")


def remove_unix_job():
    """Removes both cron jobs for Linux/macOS."""
    from crontab import CronTab

    cron = CronTab(user=True)

    main_removed = cron.remove_all(comment=JOB_COMMENT)
    refresh_removed = cron.remove_all(comment=REFRESH_JOB_COMMENT)

    if main_removed > 0 or refresh_removed > 0:
        cron.write()
        print("Success! All related cron jobs have been removed.")
    else:
        print("No related cron jobs found.")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["add", "remove"]:
        print("Usage: python setup_scheduler.py [add|remove]")
        sys.exit(1)

    action = sys.argv[1]

    # Detect OS and run the appropriate functions
    if sys.platform.startswith("win"):
        if action == "add":
            setup_windows_task()
        elif action == "remove":
            remove_windows_task()
    else:
        try:
            from crontab import CronTab
        except ImportError:
            print(
                "ERROR: The 'python-crontab' library is required. Please run: pip install python-crontab"
            )
            sys.exit(1)

        if action == "add":
            setup_unix_job()
        elif action == "remove":
            remove_unix_job()
