import logging
import os
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from rich.logging import RichHandler

LOGGER_LEVEL = os.getenv("LOGGER_LEVEL", "WARNING")
logging.basicConfig(level=LOGGER_LEVEL, format="%(message)s", handlers=[RichHandler()])
logger = logging.getLogger("LocalAuth")

class LocalAuth:
    def __init__(
        self,
        user_credentials: str = "secrets/user_token.pickle",
        app_credentials: str = "secrets/app_credentials.json"
    ):
        self.user_credentials = user_credentials
        self.app_credentials = app_credentials
        self.service = self.get_service()

    def get_service(self):
        creds = self._read_token(self.user_credentials)

        if not creds or not creds.valid:
            try:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
            except Exception as e:
                logger.warning(f"Failed to refresh credentials: {e}")
                creds = None

            if not creds:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.app_credentials,
                    ["https://www.googleapis.com/auth/gmail.modify"],
                )
                creds = flow.run_local_server(port=8080)
                self._write_token(creds, self.user_credentials)

        return build("gmail", "v1", credentials=creds)

    def _read_token(self, blob_name: str):
        """Reads token from a local file."""
        if os.path.exists(blob_name):
            with open(blob_name, "rb") as token:
                return pickle.load(token)
        return None

    def _write_token(self, creds, blob_name: str):
        """Writes token to a local file."""
        with open(blob_name, "wb") as token:
            pickle.dump(creds, token)
