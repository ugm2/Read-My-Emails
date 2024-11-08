import json

from rich import print

from emails.email_fetcher import EmailFetcher
from emails.parsers.tldr_content_parser import TLDRContentParser


def main():
    email_fetcher = EmailFetcher()
    query = "TLDR"
    emails = email_fetcher.fetch_emails(query, 2)
    articles = email_fetcher.get_articles_from_emails(emails, TLDRContentParser())

    for article in articles:
        print("\n" + "="*80)
        print(json.dumps(article, indent=2, ensure_ascii=False))
        
    print(f"Extracted {len(articles)} articles from {query}")


if __name__ == "__main__":
    main()
