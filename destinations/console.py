from typing import Dict
from interfaces import IDestination
from config import settings
from logger_setup import log


class ConsoleDestination(IDestination):
    """A destination that prints content to the console."""

    def post(self, content: Dict) -> bool:
        """Prints the text content to the screen."""
        text_to_post = content.get(settings.TEXT_COLUMN_NAME)
        if text_to_post:
            log.info("----------------------------------------")
            log.info(f"Simulating post to destination...")
            log.info(f"Content: '{text_to_post}'")
            log.info("----------------------------------------")
            return True
        else:
            log.warning(
                f"No text found in content item using key '{settings.TEXT_COLUMN_NAME}'."
            )
            return False
