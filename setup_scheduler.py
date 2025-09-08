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
import tempfile
import textwrap
import datetime


def setup_windows_task(frequency: int):
    """
    Creates or updates all tasks in Windows Task Scheduler using a robust XML
    definition with a dynamic StartBoundary to ensure compatibility.
    """
    (
        project_path,
        pythonw_path,
        main_script_path,
        refresh_script_path,
        cleanup_script_path,
    ) = get_paths()

    # --- NEW: Generate a dynamic, timezone-aware timestamp ---
    # This is the key fix. It creates a timestamp like '2025-09-08T21:02:49.123456+05:00'
    start_boundary_dt = datetime.datetime.now(datetime.timezone.utc).astimezone()
    start_boundary_str = start_boundary_dt.isoformat()

    XML_TEMPLATE = textwrap.dedent(
        """\
    <?xml version="1.0" encoding="UTF-16"?>
    <Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
      <RegistrationInfo>
        <Description>{description}</Description>
      </RegistrationInfo>
      <Triggers>
        {trigger}
      </Triggers>
      <Principals>
        <Principal id="Author">
          <UserId>{user_id}</UserId>
          <LogonType>InteractiveToken</LogonType>
          <RunLevel>HighestAvailable</RunLevel>
        </Principal>
      </Principals>
      <Settings>
        <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
        <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
        <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
        <AllowHardTerminate>true</AllowHardTerminate>
        <StartWhenAvailable>true</StartWhenAvailable>
        <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
        <IdleSettings>
          <StopOnIdleEnd>true</StopOnIdleEnd>
          <RestartOnIdle>false</RestartOnIdle>
        </IdleSettings>
        <AllowStartOnDemand>true</AllowStartOnDemand>
        <Enabled>true</Enabled>
        <Hidden>false</Hidden>
        <RunOnlyIfIdle>false</RunOnlyIfIdle>
        <WakeToRun>false</WakeToRun>
        <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
        <Priority>7</Priority>
      </Settings>
      <Actions Context="Author">
        <Exec>
          <Command>"{command}"</Command>
          <Arguments>{arguments}</Arguments>
          <WorkingDirectory>{workdir}</WorkingDirectory>
        </Exec>
      </Actions>
    </Task>
    """
    )

    # --- MODIFIED: Trigger Definitions with placeholder and new TimeTrigger ---
    main_trigger = f"""
        <TimeTrigger>
          <Repetition>
            <Interval>PT{frequency}M</Interval>
            <StopAtDurationEnd>false</StopAtDurationEnd>
          </Repetition>
          <StartBoundary>{{start_boundary}}</StartBoundary>
          <Enabled>true</Enabled>
        </TimeTrigger>
    """
    refresh_trigger = """
        <CalendarTrigger>
          <StartBoundary>{start_boundary}</StartBoundary>
          <ScheduleByDay>
            <DaysInterval>1</DaysInterval>
          </ScheduleByDay>
        </CalendarTrigger>
    """
    cleanup_trigger = """
        <CalendarTrigger>
          <StartBoundary>{start_boundary}</StartBoundary>
          <ScheduleByWeek>
            <DaysOfWeek>
              <Sunday />
            </DaysOfWeek>
            <WeeksInterval>1</WeeksInterval>
          </ScheduleByWeek>
        </CalendarTrigger>
    """

    tasks_to_create = [
        {
            "name": TASK_NAME,
            "description": JOB_COMMENT,
            "script_path": main_script_path,
            "trigger": main_trigger,
        },
        {
            "name": REFRESH_TASK_NAME,
            "description": REFRESH_JOB_COMMENT,
            "script_path": refresh_script_path,
            "trigger": refresh_trigger,
        },
        {
            "name": CLEANUP_TASK_NAME,
            "description": CLEANUP_JOB_COMMENT,
            "script_path": cleanup_script_path,
            "trigger": cleanup_trigger,
        },
    ]

    try:
        current_user = subprocess.check_output("whoami", text=True).strip()
        print(f"INFO: Setting up tasks to run as user '{current_user}'.")

        for task in tasks_to_create:
            # Inject the dynamic start boundary into the trigger
            final_trigger = task["trigger"].format(start_boundary=start_boundary_str)

            xml_content = XML_TEMPLATE.format(
                description=task["description"],
                trigger=final_trigger,
                user_id=current_user,
                command=pythonw_path,
                arguments=f'"{task["script_path"]}"',
                workdir=project_path,
            )

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".xml", delete=False, encoding="utf-16"
            ) as tmp:
                tmp.write(xml_content)
                temp_xml_path = tmp.name

            try:
                command = [
                    "schtasks",
                    "/create",
                    "/TN",
                    task["name"],
                    "/XML",
                    temp_xml_path,
                    "/F",
                ]
                subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                    creationflags=CREATE_NO_WINDOW,
                )
                print(f"- Task '{task['name']}' created/updated successfully from XML.")
            finally:
                os.remove(temp_xml_path)

        print("\nSuccess! All scheduler tasks have been set up with proper conditions.")

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        error_output = e.stderr if hasattr(e, "stderr") else str(e)
        print(
            "ERROR: Could not create a task. You may need to run this script as an Administrator."
        )
        print(f"Details: {error_output}")


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
