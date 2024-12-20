import re
from typing import Dict, List, Tuple

from emails.parsers.content_parser_interface import ContentParserInterface
from logging_config import setup_logging

logger = setup_logging(__name__)


class TLDRContentParser(ContentParserInterface):
    """
    Parser for both TLDR and TLDR AI newsletters.
    """

    def __init__(self):
        """
        Initialize TLDRContentParser with regex patterns.
        """
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

        self.reading_time_pattern = re.compile(
            r'\((?:(\d+) MINUTE READ|GITHUB REPO)\)\s*(?:\[\d+\])?$'
        )
        self.sponsor_pattern = re.compile(r'\(SPONSOR\)', re.IGNORECASE)
        self.emoji_pattern = re.compile(
            r'[\U0001F300-\U0001F9FF]|[\u2600-\u26FF\u2700-\u27BF]'
        )
        self.newsletter_endings = {
            'Love TLDR?',
            'Want to advertise in TLDR?',
            'Share your referral link',
            'Track your referrals',
            'If you have any comments'
        }
        self.link_pattern = re.compile(r'\[(\d+)\]\s*(\S+)')

        logger.info("TLDRContentParser initialized with patterns")

    def parse_content(self, content: str) -> List[Dict[str, str]]:
        logger.info("Starting content parsing")
        newsletter_type = "TLDR AI" if "TLDR AI" in content else "TLDR"
        logger.debug(f"Detected newsletter type: {newsletter_type}")
        
        articles = []
        lines = content.splitlines()
        current_section = None
        i = 0
        
        logger.debug("Extracting link mappings")
        link_mappings = self._extract_links(lines)
        logger.debug(f"Found {len(link_mappings)} link mappings")
        
        while i < len(lines):
            line = lines[i].strip()

            if not line or len(line) <= 2:
                i += 1
                continue

            if self._is_section_header(line):
                current_section = line
                logger.debug(f"Found section header: {current_section}")
                i += 1
                continue
            
            if self._is_article_start(line):
                logger.debug(f"Found article start at line {i}")
                article, i = self._parse_article(
                    lines, i, current_section, newsletter_type, link_mappings
                )
                if article:
                    logger.debug(f"Successfully parsed article: {article['title']}")
                    articles.append(article)
                continue
            
            i += 1
        
        logger.info(f"Finished parsing {len(articles)} articles from {newsletter_type}")
        return articles

    def _extract_links(self, lines: List[str]) -> Dict[str, str]:
        """Extract link mappings from the content."""
        link_mappings = {}
        for line in lines:
            line = line.strip()
            match = self.link_pattern.match(line)
            if match:
                link_number, url = match.groups()
                link_mappings[link_number] = url
        return link_mappings

    def _is_section_header(self, line: str) -> bool:
        """Check if the line is a section header."""
        return line in self.section_headers

    def _is_article_start(self, line: str) -> bool:
        """Determine if a line signifies the start of an article."""
        return self.reading_time_pattern.search(line) and not self.sponsor_pattern.search(line)

    def _is_title_line(self, line: str) -> bool:
        """Check if a line is likely to be part of a title."""
        if not line or len(line.strip()) <= 2:
            return False
        upper_count = sum(1 for c in line if c.isupper())
        lower_count = sum(1 for c in line if c.islower())
        return upper_count > lower_count

    def _should_stop_parsing(self, lines: List[str], index: int) -> bool:
        """Determine if parsing should stop for the current article."""
        if index >= len(lines):
            return True
        line = lines[index].strip()
        if not line:
            return False  # Skip empty lines
        if self._is_section_header(line):
            return True
        if self.reading_time_pattern.search(line):
            return True
        if self._is_article_start(line):
            return True
        if self._is_title_line(line) and index + 1 < len(lines) and self.reading_time_pattern.search(lines[index + 1].strip()):
            return True
        if any(ending in line for ending in self.newsletter_endings):
            return True
        return False

    def _extract_link_and_title(self, lines: List[str], index: int, link_mappings: Dict[str, str]) -> Tuple[str, str, int]:
        """Extract the link from the title line or the next line and update the title accordingly."""
        i = index
        line = lines[i].strip()
        title_line = line
        title = self.reading_time_pattern.sub('', line).strip()

        # Initialize link
        link = None

        # Check for link number in title line
        link_number_match = re.search(r'\[(\d+)\]', title_line)
        if link_number_match:
            link_number = link_number_match.group(1)
            link = link_mappings.get(link_number)
            # Remove link number from title
            title = re.sub(r'\[\d+\]', '', title).strip()
        else:
            # Check the next line for a link number
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                next_line_link_match = re.match(r'\[(\d+)\]', next_line)
                if next_line_link_match:
                    link_number = next_line_link_match.group(1)
                    link = link_mappings.get(link_number)
                    # Skip the link number line
                    i += 1

        return link, title, i

    def _parse_article(
        self, lines: List[str], start_index: int, current_section: str, newsletter_type: str, link_mappings: Dict[str, str]
    ) -> Tuple[Dict[str, str], int]:
        """Parse an article starting from the given index."""
        i = start_index
        line = lines[i].strip()
        time_match = self.reading_time_pattern.search(line)
        reading_time = int(time_match.group(1)) if time_match.group(1) else None

        # Extract link and update title and index
        link, title, i = self._extract_link_and_title(lines, i, link_mappings)

        # Check previous line for additional title content
        if start_index > 0 and self._is_title_line(lines[start_index - 1].strip()):
            prev_line = lines[start_index - 1].strip()
            title = f"{prev_line} {title}"

        # Collect content lines
        i += 1
        content_lines = []
        while i < len(lines) and not self._should_stop_parsing(lines, i):
            content_line = lines[i].strip()
            if content_line:
                content_lines.append(content_line)
            i += 1

        # Clean and assemble content
        cleaned_content = self.emoji_pattern.sub('', ' '.join(content_lines)).strip()

        article = {
            'title': title,
            'content': cleaned_content,
            'section': current_section,
            'reading_time': reading_time,
            'newsletter_type': newsletter_type,
            'link': link
        }

        return article, i

