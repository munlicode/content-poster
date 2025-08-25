import cache_manager
from sources.google_sheets import GoogleSheetsSource
from processors.today_unpublished_filter import TodayAndUnpublishedFilter
from processors.time_validator import TimeValidator
from destinations.threads import ThreadsDestination
from config import settings
from logger_setup import log


def run_pipeline():
    """
    Executes the full pipeline to fetch, schedule, post, and update content status.
    """
    log.info("\n--- Starting Content Pipeline Run ---")

    # 1. Load cache and decide if a fresh data fetch from the API is needed
    cache = cache_manager.load_cache()
    fetch_fresh_data = cache_manager.should_fetch_fresh_data(
        cache.get("last_fetch_datetime")
    )

    source = GoogleSheetsSource()
    pending_posts = cache.get("pending_posts", [])

    # 2. If a fetch is due, connect to the Google Sheets API
    if fetch_fresh_data:
        all_data = source.get_data()
        if all_data:
            # Filter for all of today's posts that haven't been published
            initial_filter = TodayAndUnpublishedFilter()
            pending_posts = initial_filter.process(all_data)
            # Save the new list to our local cache
            cache_manager.save_cache(pending_posts)
        else:
            log.info(
                "Could not retrieve data from source. Using existing cache if available."
            )
    else:
        log.info("Using cached data. No API fetch needed.")

    # If there are no posts scheduled for today, exit early
    if not pending_posts:
        log.info("No pending posts for today in cache. Nothing to do.")
        log.info("--- Pipeline Finished ---")
        return

    # 3. From the pending list, filter for posts whose scheduled time has passed
    time_validator = TimeValidator()
    posts_to_publish = time_validator.process(pending_posts)
    if not posts_to_publish:
        log.info("No posts are due to be published at this time.")
    else:
        log.info(f"Found {len(posts_to_publish)} post(s) to publish now.")

        destination = ThreadsDestination()

        # Create a copy of the list to safely modify as we process posts
        updated_pending_posts = pending_posts[:]

        for item in posts_to_publish:
            success = destination.post(item)

            if success:
                # On success, update the sheet and remove the post from our pending list
                source.update_status(
                    item.get("row_number"), settings.STATUS_OPTIONS["published"]
                )
                updated_pending_posts = [
                    p
                    for p in updated_pending_posts
                    if p.get("row_number") != item.get("row_number")
                ]
            else:
                # On failure, just update the sheet. The post remains in the cache to be retried.
                source.update_status(
                    item.get("row_number"), settings.STATUS_OPTIONS["failed"]
                )

        # If any posts were successfully published, re-save the now smaller cache
        if len(updated_pending_posts) < len(pending_posts):
            cache_manager.save_cache(updated_pending_posts)

    log.info("--- Pipeline Finished ---")


if __name__ == "__main__":
    run_pipeline()
