"""
Tests for the TLDR newsletter content parser.

These tests verify the parsing functionality for both TLDR and TLDR AI newsletters,
which have a specific format including sections like:
- HEADLINES & LAUNCHES
- RESEARCH & INNOVATION
- ENGINEERING & RESOURCES
- MISCELLANEOUS
- QUICK LINKS
- BIG TECH & STARTUPS
- SCIENCE & FUTURISTIC TECHNOLOGY
- PROGRAMMING, DESIGN & DATA SCIENCE

The parser is specifically designed to handle the unique structure and formatting
of TLDR newsletters, including reading time annotations, section headers, and
article formatting.
"""

import json
import os

from emails.parsers.tldr_content_parser import TLDRContentParser


def load_test_data(email_path: str, articles_path: str):
    """Helper function to load TLDR newsletter test data files"""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    with open(os.path.join(test_dir, email_path), 'r') as f:
        email_content = f.read()
    
    with open(os.path.join(test_dir, articles_path), 'r') as f:
        expected_articles = json.load(f)
            
    return email_content, expected_articles


def test_parse_tldr_ai_newsletter():
    """Test parsing of TLDR AI newsletter format"""
    email_content, expected_articles = load_test_data(
        'data/email_1_test.txt',
        'data/articles_1.json'
    )
    
    parser = TLDRContentParser()
    parsed_articles = parser.parse_content(email_content)
    
    assert len(parsed_articles) == len(expected_articles)
    
    for parsed, expected in zip(parsed_articles, expected_articles):
        assert parsed['title'] == expected['title']
        assert parsed['content'] == expected['content']
        assert parsed['section'] == expected['section']
        assert parsed['reading_time'] == expected['reading_time']
        assert parsed['newsletter_type'] == "TLDR AI"
        assert parsed['link'] == expected['link']


def test_parse_tldr_newsletter():
    """Test parsing of standard TLDR newsletter format"""
    email_content, expected_articles = load_test_data(
        'data/email_2_test.txt',
        'data/articles_2.json'
    )
    
    parser = TLDRContentParser()
    parsed_articles = parser.parse_content(email_content)
    
    assert len(parsed_articles) == len(expected_articles)
    
    for parsed, expected in zip(parsed_articles, expected_articles):
        assert parsed['title'] == expected['title']
        assert parsed['content'] == expected['content']
        assert parsed['section'] == expected['section']
        assert parsed['reading_time'] == expected['reading_time']
        assert parsed['newsletter_type'] == "TLDR"
        assert parsed['link'] == expected['link']


def test_tldr_link_format():
    """Test that parsed links have the correct format"""
    parser = TLDRContentParser()
    test_content = """
    HEADLINES & LAUNCHES
    
    TEST ARTICLE (2 MINUTE READ) [5]
    Some content
    
    [5] https://example.com/article?utm_source=tldrai
    """
    parsed_articles = parser.parse_content(test_content)
    
    for article in parsed_articles:
        assert 'link' in article
        assert isinstance(article['link'], str)
        assert article['link'].strip() != ""
        assert article['link'].startswith(('http://', 'https://'))
        assert 'utm_source=tldr' in article['link']


def test_tldr_parser_initialization():
    """Test TLDR parser initialization and patterns"""
    parser = TLDRContentParser()
    
    # Test TLDR-specific section headers
    expected_sections = {
        'HEADLINES & LAUNCHES',
        'RESEARCH & INNOVATION', 
        'ENGINEERING & RESOURCES',
        'MISCELLANEOUS',
        'QUICK LINKS',
        'BIG TECH & STARTUPS',
        'SCIENCE & FUTURISTIC TECHNOLOGY',
        'PROGRAMMING, DESIGN & DATA SCIENCE'
    }
    assert parser.section_headers == expected_sections
    
    # Test TLDR reading time pattern
    test_strings = [
        ('(5 MINUTE READ)', True),
        ('(GITHUB REPO)', True),
        ('(NOT A TIME)', False),
        ('5 MINUTE READ', False)
    ]
    for test_str, should_match in test_strings:
        match = parser.reading_time_pattern.search(test_str)
        assert bool(match) == should_match


def test_tldr_empty_content():
    """Test parser behavior with empty TLDR newsletter content"""
    parser = TLDRContentParser()
    parsed_articles = parser.parse_content("")
    assert len(parsed_articles) == 0


def test_tldr_malformed_content():
    """Test parser resilience with malformed TLDR newsletter content"""
    parser = TLDRContentParser()
    malformed_content = """
    QUICK LINKS
    Some Title (2 MINUTE READ) [1]
    Content without proper structure
    INVALID SECTION
    Another Title (3 MINUTE READ)
    More content
    """
    parsed_articles = parser.parse_content(malformed_content)
    assert len(parsed_articles) > 0


def test_tldr_title_detection():
    """Test the title detection for TLDR newsletter format"""
    parser = TLDRContentParser()
    
    assert parser._is_title_line("THIS IS A TLDR TITLE")
    assert parser._is_title_line("MAJOR ANNOUNCEMENT FROM GOOGLE")
    assert not parser._is_title_line("")
    assert not parser._is_title_line("Regular sentence with some CAPS")
    assert not parser._is_title_line("   ")
    assert not parser._is_title_line("a")


def test_tldr_sponsor_content_filtering():
    """Test that sponsored content is properly filtered from TLDR newsletters"""
    parser = TLDRContentParser()
    sponsored_content = """
    QUICK LINKS
    SPONSORED MESSAGE (2 MINUTE READ) (SPONSOR)
    This is sponsored content
    REAL ARTICLE (3 MINUTE READ)
    This is real content
    """
    parsed_articles = parser.parse_content(sponsored_content)
    
    for article in parsed_articles:
        assert "(SPONSOR)" not in article['title']