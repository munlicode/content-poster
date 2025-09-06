import os
import sys
from datetime import datetime
from sources.google_sheets import GoogleSheetsSource
from processors.time_validator import TimeValidator
from destinations.threads import ThreadsDestination
from destinations.instagram import InstagramDestination
from config import settings
from logger_setup import log
from helpers import get_worksheet_names

LOCK_FILE = "pipeline.lock"


def run_pipeline():
    """
    Executes the full pipeline with script and application-level locking
    to prevent race conditions and duplicate posts.
    """
    log.info("\n--- Starting Content Pipeline Run ---")
    worksheet_names = get_worksheet_names()

    for worksheet_name in worksheet_names:
        # Fetch all posts that are pending
        source = GoogleSheetsSource(worksheet_name)
        all_data = source.get_data()

        # Filter for VALID posts (your new filter)
        valid_posts = [
            post
            for post in all_data
            if post.get(settings.DATE_COLUMN_NAME)
            and post.get(settings.TIME_COLUMN_NAME)
            and post.get(settings.TEXT_COLUMN_NAME)
            and (
                str(post.get(settings.POST_ON_INSTAGRAM_COLUMN_NAME, ""))
                .strip()
                .upper()
                == "TRUE"
                or str(post.get(settings.POST_ON_THREADS_COLUMN_NAME, ""))
                .strip()
                .upper()
                == "TRUE"
            )
        ]

        log.info(f"Found {len(valid_posts)} valid row(s) with all required data.")

        if not valid_posts:
            log.info("No valid posts found. Nothing to do.")
            return

        # 2. From VALID posts, filter for those with a PENDING status
        pending_status = settings.STATUS_OPTIONS.get("pending", "Pending")
        pending_posts = [
            post
            for post in valid_posts
            if post.get(settings.STATUS_COLUMN_NAME, "").strip() in [pending_status, ""]
        ]

        if not pending_posts:
            log.info("No pending posts found. Nothing to do.")
            return

        # 3. From PENDING posts, filter for those whose time is DUE
        time_validator = TimeValidator()
        posts_to_publish = time_validator.process(pending_posts)

        if not posts_to_publish:
            log.info("No posts are due to be published at this time.")
            return

        # 4. Now, lock and process the final, correctly filtered list
        log.info(f"Found {len(posts_to_publish)} post(s) to publish. Locking them now.")
        row_numbers_to_lock = [item.get("row_number") for item in posts_to_publish]
        source.update_status_batch(
            row_numbers_to_lock, settings.STATUS_OPTIONS["publishing"]
        )

        # 4. Initialize destinations and process each "locked" post
        threads_dest = ThreadsDestination(worksheet_name)
        instagram_dest = InstagramDestination(worksheet_name)

        for item in posts_to_publish:
            row_number = item.get("row_number")
            log.info(f"Processing locked post from row {row_number}...")
            try:
                post_to_threads = (
                    str(item.get(settings.POST_ON_THREADS_COLUMN_NAME, ""))
                    .strip()
                    .upper()
                    == "TRUE"
                )
                post_to_instagram = (
                    str(item.get(settings.POST_ON_INSTAGRAM_COLUMN_NAME, ""))
                    .strip()
                    .upper()
                    == "TRUE"
                )

                # --- BUG FIX STARTS HERE ---

                # 1. Check if this post needs to be published anywhere at all.
                if not post_to_threads and not post_to_instagram:
                    log.warning(
                        f"Row {row_number} is due but not marked for any platform. "
                        "Reverting status to Pending."
                    )
                    # Revert the lock since no action is being taken
                    source.update_status(row_number, settings.STATUS_OPTIONS["pending"])
                    continue  # Skip to the next post

                # --- BUG FIX ENDS HERE ---

                threads_success = None
                instagram_success = None

                if post_to_instagram:
                    instagram_success = instagram_dest.post(item)
                if post_to_threads:
                    threads_success = threads_dest.post(item)

                # Determine the final status
                is_fully_published = True
                if post_to_instagram and not instagram_success:
                    is_fully_published = False
                if post_to_threads and not threads_success:
                    is_fully_published = False

                # Update the row with its final status
                final_status = (
                    settings.STATUS_OPTIONS["published"]
                    if is_fully_published
                    else settings.STATUS_OPTIONS["failed"]
                )
                source.update_status(row_number, final_status)
            except Exception as e:
                # If any unexpected error happens, log it and mark the post as failed
                log.error(
                    f"A critical error occurred while processing row {row_number}: {e}",
                    exc_info=True,
                )
                source.update_status(row_number, settings.STATUS_OPTIONS["failed"])
                continue  # Move to the next post
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
