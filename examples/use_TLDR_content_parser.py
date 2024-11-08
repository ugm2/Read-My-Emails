import json

from rich import print

from emails.parsers.tldr_content_parser import TLDRContentParser


def read_test_file(filename: str) -> str:
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()

def main():
    # Initialize the parser
    parser = TLDRContentParser()
    
    # Read and parse test files
    test_files = ['examples/data/email_1_test.txt', 'examples/data/email_2_test.txt']
    all_articles = []
    
    for file in test_files:
        content = read_test_file(file)
        articles = parser.parse_content(content)
        all_articles.extend(articles)
        
        print(f"\nProcessing {file}:")
        print("="*80)
        for article in articles:
            print(json.dumps(article, indent=2, ensure_ascii=False))
            print("-"*40)
    
    print(f"\nTotal articles extracted: {len(all_articles)}")

if __name__ == "__main__":
    main()