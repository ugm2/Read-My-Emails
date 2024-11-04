import base64
import logging
import os
from typing import Dict, List

from rich.logging import RichHandler

from emails.auth import LocalAuth
from emails.content_parser import ContentParserInterface

LOGGER_LEVEL = os.getenv("LOGGER_LEVEL", "WARNING")
logging.basicConfig(level=LOGGER_LEVEL, format="%(message)s", handlers=[RichHandler()])
logger = logging.getLogger("EmailFetcher")


class EmailFetcher:
    """
    A class to interact with the Gmail API, allowing fetching and parsing of emails.
    """

    def __init__(
        self,
        user_credentials: str = "secrets/user_token.pickle",
        app_credentials: str = "secrets/app_credentials.json",
    ):
        """
        Constructs all the necessary attributes for the EmailFetcher object.

        Args:
            user_credentials (str): Path to the token pickle file.
            app_credentials (str): Path to the client secret JSON file.
        """
        self.auth = LocalAuth(user_credentials, app_credentials)
        self.service = self.auth.service

    def fetch_emails(self, query: str, max_results: int = None) -> List[Dict]:
        """
        Fetches emails based on a specific query.

        Args:
            query: The query to fetch the emails.
            max_results: The maximum number of emails to fetch.

        Returns:
            A list of messages.
        """
        all_emails = []
        request = self.service.users().messages().list(userId="me", q=query)

        while request is not None:
            response = request.execute()
            logger.log(1, f"Response: {response}")
            all_emails.extend(response.get("messages", []))
            logger.info(f"Fetched {len(all_emails)} emails so far.")

            if max_results is not None and len(all_emails) >= max_results:
                logger.info("Breaking due to max_results")
                break

            request = self.service.users().messages().list_next(request, response)
            logger.log(1, f"Next request: {request}")

        return all_emails[:max_results]

    def get_email_data(self, email_id: str) -> Dict:
        """
        Gets data of a specific email.

        Args:
            email_id: The email ID.

        Returns:
            The email data.
        """
        logger.log(1, f"Fetching data for email ID: {email_id}")
        return self.service.users().messages().get(userId="me", id=email_id).execute()

    def fetch_labels(self) -> List[Dict]:
        """
        Fetches all labels from the user's Gmail account.

        Returns:
            The list of labels.
        """
        logger.info("Fetching labels from Gmail account.")
        return (
            self.service.users().labels().list(userId="me").execute().get("labels", [])
        )

    def get_label_id(self, label_name: str) -> str:
        """
        Translates a label name to its corresponding ID.

        Args:
            label_name: The label name.

        Returns:
            The label ID.

        Raises:
            ValueError: If no label is found with the given name.
        """
        labels = self.fetch_labels()
        for label in labels:
            if label["name"] == label_name:
                logger.info(f"Found label ID for {label_name}.")
                return label["id"]
        logger.error(f"No label found with the name {label_name}")
        raise ValueError(f"No label found with the name {label_name}")

    def get_body(self, email: Dict) -> str:
        """
        Gets the body of the email.

        Args:
            email: The email data.

        Returns:
            The email body.
        """
        parts = email["payload"].get("parts")
        data = parts[0]["body"]["data"] if parts else email["payload"]["body"]["data"]
        logger.info("Decoding email body.")
        return base64.urlsafe_b64decode(data).decode("utf-8")

    def get_articles_from_emails(
        self, emails: List[Dict], content_parser: ContentParserInterface
    ) -> List:
        """
        Extracts articles from a list of emails using a specific content parser.

        Args:
            emails: The list of emails.
            content_parser: The function to parse the content.

        Returns:
            A list of articles.
        """
        articles = []
        for email in emails:
            email_data = self.get_email_data(email["id"])
            content = self.get_body(email_data)
            print("--- EMAIL ---")
            print(content)
            articles += content_parser.parse_content(content)
        logger.info(f"Extracted {len(articles)} articles from emails.")
        return articles
