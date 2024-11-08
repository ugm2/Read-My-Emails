from abc import ABC, abstractmethod
from typing import Dict, List


class ContentParserInterface(ABC):
    """
    Abstract base class for content parsers.
    """

    @abstractmethod
    def parse_content(self, content: str) -> List[Dict[str, str]]:
        """
        Parse content and extract articles.

        Args:
            content: Raw email content

        Returns:
            List of dictionaries containing:
                - title: Article title
                - content: Article content
                - section: Section the article belongs to
                - reading_time: Extracted reading time in minutes
                - newsletter_type: Either 'TLDR' or 'TLDR AI'
                - link: The URL of the article
        """
        pass