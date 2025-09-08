import os
import sys
import subprocess

from config import settings

# --- Configuration ---
# Names for the main posting job
JOB_COMMENT = "Content Poster Job"
TASK_NAME = "Content Poster Script"

# Names for the token refresh job
REFRESH_JOB_COMMENT = "Content Poster Token Refresh Job"
REFRESH_TASK_NAME = "Content Poster Token Refresh Script"

# Names for the repo cleanup job
CLEANUP_JOB_COMMENT = "Repo Cleanup Job"
CLEANUP_TASK_NAME = "Repo Cleanup Script"

# --- Platform-specific settings for subprocess ---
# This flag will prevent console windows from popping up on Windows
CREATE_NO_WINDOW = 0x08000000 if sys.platform.startswith("win") else 0


def get_paths():
    """
    Determines the absolute paths for the project and Python interpreter,
    handling differences between Windows and Unix-like systems.
    """
    project_path = os.path.dirname(os.path.abspath(__file__))

    if sys.platform.startswith("win"):
        # Use pythonw.exe to run the script without a console window
        python_path = os.path.join(project_path, "venv", "Scripts", "pythonw.exe")
    else:
        python_path = os.path.join(project_path, "venv", "bin", "python")

    main_script_path = os.path.join(project_path, "main.py")
    refresh_script_path = os.path.join(project_path, "refresh_token.py")
    cleanup_script_path = os.path.join(project_path, "clean_github_uploads.py")

    return (
        project_path,
        python_path,
        main_script_path,
        refresh_script_path,
        cleanup_script_path,
    )


# --- Windows Functions (MODIFIED) ---
def setup_windows_task(frequency: int):
    """
    Creates or updates all tasks in Windows Task Scheduler, ensuring they can
    run on battery power and are not restricted by idle time.
    """
    (
        project_path,
        pythonw_path,
        main_script_path,
        refresh_script_path,
        cleanup_script_path,
    ) = get_paths()

    print(
        f"Setting up Windows Tasks: {TASK_NAME}, {REFRESH_TASK_NAME}, & {CLEANUP_TASK_NAME}"
    )

    # --- Command Strings ---
    main_command = f'"{pythonw_path}" "{main_script_path}"'
    refresh_command = f'"{pythonw_path}" "{refresh_script_path}"'
    cleanup_command = f'"{pythonw_path}" "{cleanup_script_path}"'

    # --- Task Creation Commands ---
    schtasks_main_command = [
        "schtasks",
        "/create",
        "/SC",
        "MINUTE",
        "/MO",
        str(frequency),
        "/TN",
        TASK_NAME,
        "/TR",
        f'cmd /c "cd /d {project_path} && start /B "" {main_command}"',
        "/F",
    ]
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
        f'cmd /c "cd /d {project_path} && start /B "" {refresh_command}"',
        "/F",
    ]
    schtasks_cleanup_command = [
        "schtasks",
        "/create",
        "/SC",
        "WEEKLY",
        "/D",
        "SUN",
        "/ST",
        "04:00",
        "/TN",
        CLEANUP_TASK_NAME,
        "/TR",
        f'cmd /c "cd /d {project_path} && start /B "" {cleanup_command}"',
        "/F",
    ]

    # --- NEW: Task Condition Modification Commands ---
    schtasks_main_change_cmd = ["schtasks", "/change", "/TN", TASK_NAME, "/NAC", "/I"]
    schtasks_refresh_change_cmd = [
        "schtasks",
        "/change",
        "/TN",
        REFRESH_TASK_NAME,
        "/NAC",
        "/I",
    ]
    schtasks_cleanup_change_cmd = [
        "schtasks",
        "/change",
        "/TN",
        CLEANUP_TASK_NAME,
        "/NAC",
        "/I",
    ]

    commands_to_run = [
        (schtasks_main_command, schtasks_main_change_cmd, TASK_NAME),
        (schtasks_refresh_command, schtasks_refresh_change_cmd, REFRESH_TASK_NAME),
        (schtasks_cleanup_command, schtasks_cleanup_change_cmd, CLEANUP_TASK_NAME),
    ]

    try:
        for create_cmd, change_cmd, task_name in commands_to_run:
            # Step 1: Create the task
            subprocess.run(
                create_cmd,
                check=True,
                capture_output=True,
                text=True,
                creationflags=CREATE_NO_WINDOW,
            )
            print(f"- Task '{task_name}' created/updated successfully.")

            # Step 2: Change its conditions to run on battery and ignore idle
            subprocess.run(
                change_cmd,
                check=True,
                capture_output=True,
                text=True,
                creationflags=CREATE_NO_WINDOW,
            )
            print(
                f"  -> Conditions for '{task_name}' updated (runs on battery, ignores idle)."
            )

        print("\nSuccess! All scheduler tasks have been set up with proper conditions.")

    except subprocess.CalledProcessError as e:
        print(
            "ERROR: Could not create or modify a task. You may need to run this script as an Administrator."
        )
        print(f"Details: {e.stderr}")


def remove_windows_task():
    """Deletes all tasks from Windows Task Scheduler."""
    commands_to_run = [
        ["schtasks", "/delete", "/TN", TASK_NAME, "/F"],
        ["schtasks", "/delete", "/TN", REFRESH_TASK_NAME, "/F"],
        ["schtasks", "/delete", "/TN", CLEANUP_TASK_NAME, "/F"],
    ]

    print("Removing scheduler tasks...")
    for command in commands_to_run:
        task_name_to_remove = command[3]
        try:
            # MODIFIED: Added creationflags to hide the schtasks.exe window
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                creationflags=CREATE_NO_WINDOW,
            )
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
def setup_unix_job(frequency: int):
    """Adds or updates all cron jobs for Linux/macOS."""
    from crontab import CronTab

    (
        project_path,
        python_path,
        main_script_path,
        refresh_script_path,
        cleanup_script_path,
    ) = get_paths()

    cron = CronTab(user=True)

    # Remove old jobs to avoid duplicates
    cron.remove_all(comment=JOB_COMMENT)
    cron.remove_all(comment=REFRESH_JOB_COMMENT)
    cron.remove_all(comment=CLEANUP_JOB_COMMENT)  # NEW

    # Create main job (every minute)
    main_command = f"cd {project_path} && {python_path} {main_script_path}"
    main_job = cron.new(command=main_command, comment=JOB_COMMENT)
    main_job.minute.every(frequency)

    # Create refresh job (daily at 3 AM)
    refresh_command = f"cd {project_path} && {python_path} {refresh_script_path}"
    refresh_job = cron.new(command=refresh_command, comment=REFRESH_JOB_COMMENT)
    refresh_job.setall("0 3 * * *")

    # NEW: Create cleanup job (weekly on Sunday at 4 AM)
    cleanup_command = f"cd {project_path} && {python_path} {cleanup_script_path}"
    cleanup_job = cron.new(command=cleanup_command, comment=CLEANUP_JOB_COMMENT)
    cleanup_job.setall("0 4 * * SUN")  # Cron syntax for 4:00 AM on Sunday

    cron.write()
    print("Success! All cron jobs have been set up.")
    print("To see them, run: crontab -l")


def remove_unix_job():
    """Removes all cron jobs for Linux/macOS."""
    from crontab import CronTab

    cron = CronTab(user=True)

    main_removed = cron.remove_all(comment=JOB_COMMENT)
    refresh_removed = cron.remove_all(comment=REFRESH_JOB_COMMENT)
    cleanup_removed = cron.remove_all(comment=CLEANUP_JOB_COMMENT)  # NEW

    if main_removed > 0 or refresh_removed > 0 or cleanup_removed > 0:
        cron.write()
        print("Success! All related cron jobs have been removed.")
    else:
        print("No related cron jobs found.")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["add", "remove"]:
        print("Usage: python setup_scheduler.py [add|remove]")
        sys.exit(1)

    action = sys.argv[1]
    run_frequency = 1
    if action == "add":
        run_frequency = getattr(settings, "MAIN_SCRIPT_RUN_FREQUENCY_MINUTES", 1)
        if not isinstance(run_frequency, int) or run_frequency <= 0:
            print(
                f"ERROR: 'MAIN_SCRIPT_RUN_FREQUENCY_MINUTES' in config.py must be a positive integer."
            )
            print(f"       Found value: '{run_frequency}'")
            sys.exit(1)
        print(
            f"INFO: Main script will be scheduled to run every {run_frequency} minute(s)."
        )

    if sys.platform.startswith("win"):
        if action == "add":
            setup_windows_task(frequency=run_frequency)
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
            setup_unix_job(frequency=run_frequency)
        elif action == "remove":
            remove_unix_job()
