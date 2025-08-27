import os
import sys
from datetime import datetime
from sources.google_sheets import GoogleSheetsSource
from processors.time_validator import TimeValidator
from destinations.threads import ThreadsDestination
from destinations.instagram import InstagramDestination
from config import settings
from logger_setup import log

LOCK_FILE = "pipeline.lock"


def run_pipeline():
    """
    Executes the full pipeline with script and application-level locking
    to prevent race conditions and duplicate posts.
    """
    log.info("\n--- Starting Content Pipeline Run ---")

    # 1. Fetch all posts that are pending
    source = GoogleSheetsSource()
    all_data = source.get_data()

    # Filter for posts that are ready to be considered for publishing
    pending_status = settings.STATUS_OPTIONS.get("pending", "Pending")
    pending_posts = [
        post
        for post in all_data
        if post.get(settings.STATUS_COLUMN_NAME, "").strip() in [pending_status, ""]
    ]

    if not pending_posts:
        log.info("No pending posts found. Nothing to do.")
        return

    # 2. From the pending list, find posts whose scheduled time has passed
    time_validator = TimeValidator()
    posts_to_publish = time_validator.process(pending_posts)

    if not posts_to_publish:
        log.info("No posts are due to be published at this time.")
        return

    # 3. APPLICATION-LEVEL LOCK: Mark posts as "Publishing" in the Google Sheet
    log.info(f"Found {len(posts_to_publish)} post(s) to publish. Locking them now.")
    row_numbers_to_lock = [item.get("row_number") for item in posts_to_publish]
    source.update_status_batch(
        row_numbers_to_lock, settings.STATUS_OPTIONS["publishing"]
    )

    # 4. Initialize destinations and process each "locked" post
    threads_dest = ThreadsDestination()
    instagram_dest = InstagramDestination()

    for item in posts_to_publish:
        row_number = item.get("row_number")
        log.info(f"Processing locked post from row {row_number}...")

        post_to_threads = str(
            item.get(settings.POST_ON_THREADS_COLUMN_NAME, "")
        ).strip().lower() in ["true", "1"]
        post_to_instagram = str(
            item.get(settings.POST_ON_INSTAGRAM_COLUMN_NAME, "")
        ).strip().lower() in ["true", "1"]

        threads_success = None
        instagram_success = None

        if post_to_threads:
            threads_success = threads_dest.post(item)
        if post_to_instagram:
            instagram_success = instagram_dest.post(item)

        # Determine the final status
        is_fully_published = True
        if post_to_threads and not threads_success:
            is_fully_published = False
        if post_to_instagram and not instagram_success:
            is_fully_published = False

        # Update the row with its final status
        final_status = (
            settings.STATUS_OPTIONS["published"]
            if is_fully_published
            else settings.STATUS_OPTIONS["failed"]
        )
        source.update_status(row_number, final_status)

    log.info("--- Pipeline Finished ---")


if __name__ == "__main__":
    # SCRIPT-LEVEL LOCK: Prevents the script from running more than once at a time.
    if os.path.exists(LOCK_FILE):
        log.warning(
            f"Lock file '{LOCK_FILE}' exists. Another instance may be running. Exiting."
        )
        sys.exit(1)

    try:
        # Create the lock file to signal the script is running
        with open(LOCK_FILE, "w") as f:
            f.write(str(datetime.now()))

        run_pipeline()

    finally:
        # CRITICAL: Always remove the lock file when the script is done,
        # even if it crashes.
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
            log.info("Lock file removed.")
