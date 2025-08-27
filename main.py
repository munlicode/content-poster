import cache_manager
from sources.google_sheets import GoogleSheetsSource
from processors.today_unpublished_filter import TodayAndUnpublishedFilter
from processors.time_validator import TimeValidator
from destinations.threads import ThreadsDestination
from destinations.instagram import InstagramDestination
from config import settings
from logger_setup import log


def run_pipeline():
    """
    Executes the full pipeline to fetch, schedule, post, and update content status.
    """
    log.info("\n--- Starting Content Pipeline Run ---")

    # 1. Load cache and decide if a fresh data fetch is needed
    cache = cache_manager.load_cache()
    fetch_fresh_data = cache_manager.should_fetch_fresh_data(
        cache.get("last_fetch_datetime")
    )

    source = GoogleSheetsSource()
    pending_posts = cache.get("pending_posts", [])

    # 2. If a fetch is due, connect to the Google Sheets API
    if fetch_fresh_data:
        log.info("Fetching fresh data from Google Sheets.")
        all_data = source.get_data()
        if all_data:
            initial_filter = TodayAndUnpublishedFilter()
            pending_posts = initial_filter.process(all_data)
            cache_manager.save_cache(pending_posts)
            log.info(f"Found {len(pending_posts)} pending posts for today.")
        else:
            log.warning(
                "Could not retrieve data from source. Using existing cache if available."
            )
    else:
        log.info("Using cached data. No fresh API fetch needed.")

    if not pending_posts:
        log.info("No pending posts for today. Exiting.")
        log.info("--- Pipeline Finished ---")
        return

    # 3. Filter for posts whose scheduled time has passed
    time_validator = TimeValidator()
    posts_to_publish = time_validator.process(pending_posts)

    if not posts_to_publish:
        log.info("No posts are due to be published at this time.")
        log.info("--- Pipeline Finished ---")
        return

    log.info(f"Found {len(posts_to_publish)} post(s) to publish now.")

    # 4. Initialize destinations
    threads_dest = ThreadsDestination()
    instagram_dest = InstagramDestination()

    updated_pending_posts = pending_posts[:]

    # 5. Process and publish each due post
    for item in posts_to_publish:
        row_number = item.get("row_number")
        post_text = item.get("text", "No text provided")
        log.info(f"Processing post for row {row_number}: '{post_text[:50]}...'")

        post_to_threads = item.get(settings.POST_ON_THREADS, False)
        post_to_instagram = item.get(settings.POST_ON_INSTAGRAM, False)

        # Track the success status for each platform
        threads_success = None
        instagram_success = None

        if post_to_threads:
            log.info(f"Attempting to post to Threads for row {row_number}.")
            threads_success = threads_dest.post(item)
            log.info(f"Threads post success: {threads_success}")

        if post_to_instagram:
            log.info(f"Attempting to post to Instagram for row {row_number}.")
            instagram_success = instagram_dest.post(item)
            log.info(f"Instagram post success: {instagram_success}")

        # Determine the final status and whether to remove from cache
        is_fully_published = True
        final_status = settings.STATUS_OPTIONS["published"]

        # Check Threads outcome
        if post_to_threads and not threads_success:
            is_fully_published = False
            final_status = settings.STATUS_OPTIONS["failed"]

        # Check Instagram outcome
        if post_to_instagram and not instagram_success:
            is_fully_published = False
            final_status = settings.STATUS_OPTIONS["failed"]

        # If the post wasn't intended for either, do nothing
        if not post_to_threads and not post_to_instagram:
            log.warning(
                f"Row {row_number} was due but not flagged for Threads or Instagram. Skipping."
            )
            continue

        # Update the source (Google Sheet) with the final status
        source.update_status(row_number, final_status)
        log.info(f"Updated Google Sheet row {row_number} with status: '{final_status}'")

        # If all intended publications were successful, remove the post from the pending list
        if is_fully_published:
            log.info(
                f"Post for row {row_number} was successfully published to all destinations."
            )
            updated_pending_posts = [
                p for p in updated_pending_posts if p.get("row_number") != row_number
            ]
        else:
            log.warning(
                f"Post for row {row_number} failed on at least one destination. It will be retried."
            )

    # 6. If any posts were successfully processed, update the cache
    if len(updated_pending_posts) < len(pending_posts):
        log.info("Updating cache with remaining pending posts.")
        cache_manager.save_cache(updated_pending_posts)

    log.info("--- Pipeline Finished ---")


if __name__ == "__main__":
    run_pipeline()
