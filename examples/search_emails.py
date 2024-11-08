from rich import print

from emails.email_indexer import EmailIndexingService
from emails.email_searcher import EmailSearchSystem


def main():
    search_system = EmailSearchSystem()
    indexing_service = EmailIndexingService(search_system=search_system)
    
    print("Indexing new emails from TLDR newsletter...")
    new_count = indexing_service.index_new_emails("TLDR", max_results=10)
    print(f"Added {new_count} new articles to the search index")
    
    print("\nEntering search mode...")
    query = "What are the latest developments in AI chips?"
    print(f"\nSearching for: {query}")
    results = search_system.search(query, k=3)
    
    if not results:
        print("\nNo results found.")
        return
        
    print("\nSearch Results:\n")
    print(results)


if __name__ == "__main__":
    main()