import json
from pathlib import Path
from typing import Set

from .email_fetcher import EmailFetcher
from .email_searcher import EmailSearchSystem
from .parsers.tldr_content_parser import TLDRContentParser


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
        if self.processed_emails_path.exists():
            with open(self.processed_emails_path, 'r') as f:
                return set(json.load(f))
        return set()
    
    def _save_processed_emails(self):
        with open(self.processed_emails_path, 'w') as f:
            json.dump(list(self.processed_emails), f)
    
    def index_new_emails(self, query: str, max_results: int = 100) -> int:
        emails = self.email_fetcher.fetch_emails(query, max_results)
        
        # Filter out already processed emails
        new_emails = []
        for email in emails:
            email_id = email["id"]
            if email_id not in self.processed_emails:
                new_emails.append(email)
        
        if not new_emails:
            return 0
            
        articles = self.email_fetcher.get_articles_from_emails(new_emails, self.content_parser)
        
        new_count = self.search_system.add_emails(articles)
        
        self.processed_emails.update(email["id"] for email in new_emails)
        
        self._save_processed_emails()
        
        return new_count 