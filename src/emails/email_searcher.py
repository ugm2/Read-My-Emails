import logging
import os
from typing import Dict, List

from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from rich.logging import RichHandler

LOGGER_LEVEL = os.getenv("LOGGER_LEVEL", "WARNING")
logging.basicConfig(level=LOGGER_LEVEL, format="%(message)s", handlers=[RichHandler()])
logger = logging.getLogger("EmailSearchSystem")

class EmailSearchSystem:
    def __init__(
        self, 
        base_dir: str = ".email_search",
        model_name: str = "mxbai-embed-large"
    ):
        """
        Initialize the email search system.
        
        Args:
            base_dir: Base directory to store all search system files
            model_name: Name of the Ollama model to use for embeddings
        """
        # Create base directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)
        
        # Store all paths relative to base directory
        self.index_path = os.path.join(base_dir, "faiss_index")
        self.embeddings = OllamaEmbeddings(model=model_name)
        
        # Load or create vector store with cosine similarity
        if os.path.exists(self.index_path):
            self.vector_store = FAISS.load_local(
                self.index_path, 
                self.embeddings,
                allow_dangerous_deserialization=True,
                normalize_L2=True  # Enable cosine similarity
            )
        else:
            self.vector_store = None

    def add_emails(self, emails: List[Dict]) -> int:
        new_emails = []
        texts = []
        metadatas = []
        
        for email in emails:
            full_text = f"Title: {email['title']}\n\nContent: {email['content']}"
            metadata = {
                "title": email["title"],
                "section": email.get("section", ""),
                "reading_time": email.get("reading_time"),
                "newsletter_type": email.get("newsletter_type", ""),
                "link": email.get("link", "")
            }
            
            texts.append(full_text)
            metadatas.append(metadata)
            new_emails.append(email)

        if texts:
            if self.vector_store is None:
                self.vector_store = FAISS.from_texts(
                    texts, 
                    self.embeddings, 
                    metadatas=metadatas,
                    normalize_L2=True  # Enable cosine similarity
                )
            else:
                self.vector_store.add_texts(texts, metadatas=metadatas)
                
            self.vector_store.save_local(self.index_path)
        
        logger.info(f"Added {len(new_emails)} new emails to the index")
        return len(new_emails)

    def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for relevant email content using cosine similarity.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents with their metadata, sorted by similarity
            (scores between -1 and 1, where 1 is most similar)
        """
        if self.vector_store is None:
            logger.warning("No emails indexed yet")
            return []
            
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        formatted_results = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": round(float(score), 3)
            }
            for doc, score in results
        ]
        
        # Sort by similarity score in descending order
        formatted_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return formatted_results