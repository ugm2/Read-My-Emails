import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Dict, List

from rich.logging import RichHandler

LOGGER_LEVEL = os.environ.get("LOGGER_LEVEL", "WARNING").upper()
logging.basicConfig(
    level=LOGGER_LEVEL, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger("TLDRContentParser")


class ContentParserInterface(ABC):
    """
    Abstract base class for content parsers.
    """

    @abstractmethod
    def parse_content(self, content: str) -> List[Dict[str, str]]:
        """
        Parse content and extract articles.
        
        Args:
            content: Raw email content
            
        Returns:
            List of dictionaries containing:
                - title: Article title
                - content: Article content
                - section: Section the article belongs to
                - reading_time: Extracted reading time in minutes
                - newsletter_type: Either 'TLDR' or 'TLDR AI'
        """
        pass


class TLDRContentParser(ContentParserInterface):
    """
    Parser for both TLDR and TLDR AI newsletters.
    """

    def __init__(self):
        """
        Initialize TLDRContentParser with regex patterns.
        """
        # Known section headers
        self.section_headers = {
            'HEADLINES & LAUNCHES',
            'RESEARCH & INNOVATION', 
            'ENGINEERING & RESOURCES',
            'MISCELLANEOUS',
            'QUICK LINKS',
            'BIG TECH & STARTUPS',
            'SCIENCE & FUTURISTIC TECHNOLOGY',
            'PROGRAMMING, DESIGN & DATA SCIENCE'
        }
        
        # Updated patterns
        self.reading_time_pattern = re.compile(r'\((?:(\d+) MINUTE READ|GITHUB REPO)\)\s*(?:\[\d+\])?$')
        self.sponsor_pattern = re.compile(r'\(SPONSOR\)', re.IGNORECASE)
        
        # Add emoji pattern
        self.emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF]|[\u2600-\u26FF\u2700-\u27BF]')
        
        # Add patterns for newsletter endings
        self.newsletter_endings = {
            'Love TLDR?',
            'Want to advertise in TLDR?',
            'Share your referral link',
            'Track your referrals',
            'If you have any comments'
        }
        
        logger.info("TLDRContentParser initialized with patterns")

    def _is_title_line(self, line: str) -> bool:
        """Check if a line could be part of a title"""
        if not line or len(line.strip()) <= 2:
            return False
        
        upper_count = sum(1 for c in line if c.isupper())
        lower_count = sum(1 for c in line if c.islower())
        
        return upper_count > lower_count * 2

    def parse_content(self, content: str) -> List[Dict[str, str]]:
        newsletter_type = "TLDR AI" if "TLDR AI" in content else "TLDR"
        articles = []
        
        lines = content.splitlines()
        current_section = None
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line or len(line) <= 2:
                i += 1
                continue
                
            # Update section if we hit a section header
            if line in self.section_headers:
                current_section = line
                i += 1
                continue
            
            # Check if current line has reading time marker
            time_match = self.reading_time_pattern.search(line)
            if time_match and not self.sponsor_pattern.search(line):
                # Extract title and reading time
                title = self.reading_time_pattern.sub('', line).strip()
                reading_time = int(time_match.group(1)) if time_match.group(1) else None
                
                # Check previous line for additional title content
                if i > 0 and self._is_title_line(lines[i-1].strip()):
                    prev_line = lines[i-1].strip()
                    title = f"{prev_line} {title}"
                
                # Collect content
                content_lines = []
                i += 1
                while i < len(lines):
                    content_line = lines[i].strip()
                    
                    # Stop conditions
                    if not content_line:
                        i += 1
                        continue
                    if content_line in self.section_headers:
                        break
                    if self.reading_time_pattern.search(content_line):
                        break
                    if self._is_title_line(content_line) and i + 1 < len(lines) and self.reading_time_pattern.search(lines[i+1].strip()):
                        break
                    # Add new stop condition for newsletter endings
                    if any(ending in content_line for ending in self.newsletter_endings):
                        break
                    
                    content_lines.append(content_line)
                    i += 1
                
                # Add article if we have both title and content
                if title and content_lines:
                    # Clean content by removing emojis
                    cleaned_content = self.emoji_pattern.sub('', ' '.join(line.strip() for line in content_lines if line.strip())).strip()
                    articles.append({
                        'title': title,
                        'content': cleaned_content,
                        'section': current_section,
                        'reading_time': reading_time,
                        'newsletter_type': newsletter_type
                    })
                continue
                
            i += 1
        
        logger.info(f"Parsed {len(articles)} articles from {newsletter_type}")
        return articles
