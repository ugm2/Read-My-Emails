from typing import Any, Dict, Optional

from fastapi import Depends

from emails.email_indexer import EmailIndexingService
from emails.email_searcher import EmailSearchSystem
from logging_config import setup_logging

from ..core.config import Settings, get_settings
from ..models.emails import SearchResponse

logger = setup_logging(__name__)

class EmailService:
    _instance: Optional['EmailService'] = None
    
    def __init__(self, settings: Settings):
        logger.debug("Initializing EmailService")
        self.settings = settings
        self.search_system = EmailSearchSystem(
            base_dir=settings.base_dir,
            model_name=settings.model_name
        )
        self.indexing_service = EmailIndexingService(
            search_system=self.search_system
        )
        logger.info("EmailService initialized successfully")
    
    @classmethod
    def get_instance(cls, settings: Settings = Depends(get_settings)) -> 'EmailService':
        logger.debug("Getting EmailService instance")
        if cls._instance is None:
            logger.info("Creating new EmailService instance")
            cls._instance = cls(settings)
        return cls._instance
    
    def search(self, query: str, limit: int = 5, min_score: float = 0.0) -> SearchResponse:
        logger.info(f"Searching emails with query='{query}', limit={limit}, min_score={min_score}")
        
        try:
            results = self.search_system.search(query, k=limit)
            filtered_results = [
                result for result in results 
                if result.get("similarity_score", 0) >= min_score
            ]
            
            logger.debug(f"Found {len(filtered_results)} results after filtering")
            
            return SearchResponse(
                results=filtered_results,
                total=len(filtered_results),
                query=query
            )
        except Exception as e:
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            raise
    
    async def index_emails(self, query: str, max_results: int) -> Dict[str, Any]:
        logger.info(f"Indexing emails with query='{query}', max_results={max_results}")
        
        try:
            new_count = self.indexing_service.index_new_emails(query, max_results)
            result = {
                "status": "success",
                "new_count": new_count,
                "message": f"Indexed {new_count} new articles"
            }
            logger.info(f"Successfully indexed {new_count} new articles")
            return result
            
        except Exception as e:
            logger.error(f"Failed to index emails: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            } 
    
    def get_total_articles(self) -> int:
        """
        Get the total number of indexed articles.
        
        Returns:
            int: Total number of articles in the search system
        """
        logger.info("Getting total number of indexed articles")
        return self.search_system.get_total_articles()