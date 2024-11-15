from typing import List, Optional

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=10000)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
class EmailMetadata(BaseModel):
    title: str
    section: Optional[str] = None
    reading_time: Optional[int] = None
    newsletter_type: Optional[str] = None
    link: Optional[str] = None

class SearchResult(BaseModel):
    content: str
    metadata: EmailMetadata
    similarity_score: float

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str 