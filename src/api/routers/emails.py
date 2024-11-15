from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from logging_config import setup_logging

from ..models.emails import SearchQuery, SearchResponse
from ..services.email_service import EmailService

logger = setup_logging(__name__)

router = APIRouter(prefix="/api/emails", tags=["emails"])

@router.post("/index")
async def index_emails(
    query: str,
    max_results: int,
    email_service: EmailService = Depends(EmailService.get_instance)
) -> Dict[str, Any]:
    """Index new emails from a specific query"""
    logger.info(f"Received index request with query='{query}', max_results={max_results}")
    
    try:
        result = await email_service.index_emails(query, max_results)
        if result["status"] == "error":
            logger.error(f"Indexing failed: {result['message']}")
            raise HTTPException(status_code=500, detail=result["message"])
        logger.info(f"Successfully indexed emails: {result['message']}")
        return result
    except Exception as e:
        logger.error(f"Unexpected error during indexing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_emails(
    query: SearchQuery,
    email_service: EmailService = Depends(EmailService.get_instance)
) -> SearchResponse:
    """Search indexed emails"""
    logger.info(f"Received search request: {query}")
    
    try:
        response = email_service.search(
            query.query,
            limit=query.limit,
            min_score=query.min_score
        )
        logger.info(f"Search completed successfully with {response.total} results")
        return response
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/count")
async def get_article_count(
    email_service: EmailService = Depends(EmailService.get_instance)
) -> Dict[str, int]:
    """Get the total number of indexed articles"""
    logger.info("Received request for article count")
    try:
        count = email_service.get_total_articles()
        logger.info(f"Found {count} indexed articles")
        return {"total": count}
    except Exception as e:
        logger.error(f"Failed to get article count: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 