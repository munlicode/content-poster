import re
from typing import List


def parse_and_clean_urls(raw_url_string: str) -> List[str]:
    """
    Takes a raw string of URLs and robustly parses it into a clean list.
    Handles separators like commas, semicolons, and any whitespace,
    while also stripping hidden characters from each URL.
    """
    if not raw_url_string:
        return []

    # Split the string by any comma, semicolon, or whitespace character
    split_urls = re.split(r"[\s,;]+", raw_url_string)

    # Clean each resulting URL and filter out any empty strings
    cleaned_urls = [url.strip() for url in split_urls if url.strip()]

    return cleaned_urls
