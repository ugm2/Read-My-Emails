import os
from typing import Dict, List

from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings

from logging_config import setup_logging

logger = setup_logging(__name__)

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
        logger.info(f"Initializing EmailSearchSystem with base_dir={base_dir}, model={model_name}")
        # Create base directory if it doesn't exist
        os.makedirs(base_dir, exist_ok=True)
        
        # Store all paths relative to base directory
        self.index_path = os.path.join(base_dir, "faiss_index")
        self.embeddings = OllamaEmbeddings(model=model_name)
        
        # Load or create vector store with cosine similarity
        if os.path.exists(self.index_path):
            logger.info(f"Loading existing FAISS index from {self.index_path}")
            self.vector_store = FAISS.load_local(
                self.index_path, 
                self.embeddings,
                allow_dangerous_deserialization=True,
                normalize_L2=True  # Enable cosine similarity
            )
            logger.debug("FAISS index loaded successfully")
        else:
            logger.info("No existing index found, starting fresh")
            self.vector_store = None

    def add_articles(self, articles: List[Dict]) -> int:
        logger.debug(f"Processing {len(articles)} articles for indexing")
        
        if not articles:
            logger.warning("No articles provided for indexing")
            return 0
            
        new_articles = []
        texts = []
        metadatas = []
        
        for i, article in enumerate(articles):
            logger.debug(f"Processing article {i+1}/{len(articles)}")
            full_text = f"Title: {article['title']}\n\nContent: {article['content']}"
            metadata = {
                "title": article["title"],
                "section": article.get("section", ""),
                "reading_time": article.get("reading_time"),
                "newsletter_type": article.get("newsletter_type", ""),
                "link": article.get("link", "")
            }
            
            texts.append(full_text)
            metadatas.append(metadata)
            new_articles.append(article)

        if texts:
            if self.vector_store is None:
                logger.info("Creating new FAISS index")
                self.vector_store = FAISS.from_texts(
                    texts, 
                    self.embeddings, 
                    metadatas=metadatas,
                    normalize_L2=True  # Enable cosine similarity
                )
            else:
                logger.info("Adding texts to existing FAISS index")
                self.vector_store.add_texts(texts, metadatas=metadatas)
            
            logger.info(f"Saving index to {self.index_path}")
            self.vector_store.save_local(self.index_path)
            logger.debug("Index saved successfully")

        return len(new_articles)

    def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for relevant article content using cosine similarity.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents with their metadata, sorted by similarity
            (scores between -1 and 1, where 1 is most similar)
        """
        logger.info(f"Searching for: '{query}' with k={k}")
        
        if self.vector_store is None:
            logger.error("Search attempted but no articles have been indexed yet")
            return []
        
        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            logger.debug(f"Raw search returned {len(results)} results")
            
            formatted_results = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": round(float(score), 3)
                }
                for doc, score in results
            ]
            
            formatted_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            for i, result in enumerate(formatted_results):
                logger.debug(f"Result {i+1}: Score={result['similarity_score']}, "
                           f"Title={result['metadata']['title']}")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed with error: {str(e)}", exc_info=True)
            return []

    def get_total_articles(self) -> int:
        """
        Get the total number of articles in the vector store.
        
        Returns:
            int: Total number of indexed articles, or 0 if no articles are indexed
        """
        logger.info("Getting total number of indexed articles")
        if self.vector_store is None:
            logger.debug("No articles indexed yet")
            return 0
        return len(self.vector_store.index_to_docstore_id)