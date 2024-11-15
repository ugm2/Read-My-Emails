import json
from pathlib import Path
from typing import Set

from logging_config import setup_logging

from .email_fetcher import EmailFetcher
from .email_searcher import EmailSearchSystem
from .parsers.tldr_content_parser import TLDRContentParser

logger = setup_logging(__name__)


class EmailIndexingService:
    def __init__(self, cache_dir: str = ".email_search", search_system: EmailSearchSystem = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.processed_emails_path = self.cache_dir / "processed_emails.json"
        self.processed_emails: Set[str] = self._load_processed_emails()
        
        self.email_fetcher = EmailFetcher()
        self.content_parser = TLDRContentParser()
        self.search_system = search_system if search_system else EmailSearchSystem()
    
    def _load_processed_emails(self) -> Set[str]:
        logger.debug(f"Loading processed emails from {self.processed_emails_path}")
        if self.processed_emails_path.exists():
            try:
                with open(self.processed_emails_path, 'r') as f:
                    emails = set(json.load(f))
                    logger.info(f"Loaded {len(emails)} processed email IDs")
                    return emails
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse processed emails file: {e}", exc_info=True)
                return set()
        logger.info("No processed emails file found, starting fresh")
        return set()
    
    def _save_processed_emails(self):
        logger.debug(f"Saving {len(self.processed_emails)} processed email IDs")
        try:
            with open(self.processed_emails_path, 'w') as f:
                json.dump(list(self.processed_emails), f)
            logger.info("Successfully saved processed emails")
        except IOError as e:
            logger.error(f"Failed to save processed emails: {e}", exc_info=True)
    
    def index_new_emails(self, query: str, max_results: int = 100) -> int:
        logger.info(f"Starting email indexing with query='{query}', max_results={max_results}")
        
        try:
            emails = self.email_fetcher.fetch_emails(query, max_results)
            logger.debug(f"Fetched {len(emails)} total emails")
            
            new_emails = []
            for email in emails:
                email_id = email["id"]
                if email_id not in self.processed_emails:
                    new_emails.append(email)
                else:
                    logger.debug(f"Skipping already processed email {email_id}")
            
            logger.info(f"Found {len(new_emails)} new unprocessed emails")
            
            if not new_emails:
                logger.info("No new emails to process")
                return 0
            
            logger.debug("Extracting articles from emails")
            articles = self.email_fetcher.get_articles_from_emails(new_emails, self.content_parser)
            logger.info(f"Extracted {len(articles)} articles from {len(new_emails)} emails")
            
            new_count = self.search_system.add_articles(articles)
            
            self.processed_emails.update(email["id"] for email in new_emails)
            self._save_processed_emails()
            
            logger.info(f"Successfully indexed {new_count} new articles")
            return new_count
            
        except Exception as e:
            logger.error(f"Failed to index new emails: {e}", exc_info=True)
            return 0