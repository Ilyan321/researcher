"""Web Reader Tool for Researcher AI.

Fetches web pages, extracts clean readable text, strips boilerplate and scripts,
and returns structured textual content for deep analysis.
"""

import json
import re
import urllib.request
import urllib.error
from typing import Optional
from config import USER_AGENT, REQUEST_TIMEOUT

try:
    from crewai.tools import tool
except ImportError:
    def tool(name_or_func=None):
        def decorator(func):
            func.is_tool = True
            return func
        if callable(name_or_func):
            return decorator(name_or_func)
        return decorator

MAX_CONTENT_CHARS = 4000


def read_url_content(url: str, max_chars: int = MAX_CONTENT_CHARS) -> str:
    """Fetch and clean the textual content of a web page."""
    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")):
        return json.dumps({
            "status": "error",
            "message": f"Invalid URL format: '{clean_url}'. URL must start with http:// or https://",
            "url": clean_url,
        })

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        req = urllib.request.Request(clean_url, headers=headers)
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            content_type = response.headers.get("Content-Type", "").lower()
            
            # Reject non-HTML/text binary files (PDFs, images, zip)
            if any(b in content_type for b in ["image/", "video/", "audio/", "application/zip", "application/octet-stream"]):
                return json.dumps({
                    "status": "error",
                    "message": f"Unsupported media type: {content_type}",
                    "url": clean_url,
                })

            raw_html = response.read().decode("utf-8", errors="replace")

    except urllib.error.HTTPError as e:
        return json.dumps({
            "status": "error",
            "message": f"HTTP {e.code}: {e.reason}",
            "url": clean_url,
        })
    except urllib.error.URLError as e:
        return json.dumps({
            "status": "error",
            "message": f"Network connection error: {str(e.reason)}",
            "url": clean_url,
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to retrieve page: {str(e)}",
            "url": clean_url,
        })

    # Extract Title and Clean Text using BeautifulSoup if available, else regex
    page_title = "Untitled Page"
    cleaned_text = ""

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(raw_html, "html.parser")

        # Extract title
        if soup.title and soup.title.string:
            page_title = soup.title.string.strip()

        # Remove irrelevant elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg"]):
            element.decompose()

        cleaned_text = soup.get_text(separator=" ", strip=True)

    except ImportError:
        # Regex fallback if beautifulsoup is not installed
        title_match = re.search(r"<title>(.*?)</title>", raw_html, re.IGNORECASE | re.DOTALL)
        if title_match:
            page_title = title_match.group(1).strip()

        no_script = re.sub(r"<(script|style|nav|footer|header|aside).*?>.*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
        no_tags = re.sub(r"<[^>]+>", " ", no_script)
        cleaned_text = re.sub(r"\s+", " ", no_tags).strip()

    # Normalize whitespace
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

    if not cleaned_text:
        return json.dumps({
            "status": "warning",
            "message": "Page loaded successfully but contained no readable text content.",
            "url": clean_url,
            "title": page_title,
        })

    truncated = len(cleaned_text) > max_chars
    final_text = cleaned_text[:max_chars]

    return json.dumps({
        "status": "success",
        "url": clean_url,
        "title": page_title,
        "content": final_text,
        "is_truncated": truncated,
        "character_count": len(final_text),
    }, indent=2)


@tool("web_reader")
def web_reader_tool(url: str) -> str:
    """Fetch and read the full text content of a specific web page URL.
    Pass a valid HTTP or HTTPS URL discovered during search.
    Returns cleaned text content, page title, and metadata.
    """
    return read_url_content(url)
