"""Utility helper functions."""

import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    # Replace spaces with underscores
    filename = filename.replace(" ", "_")
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def generate_hash(text: str) -> str:
    """Generate SHA256 hash of text.

    Args:
        text: Input text

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(text.encode()).hexdigest()


def is_valid_url(url: str) -> bool:
    """Check if URL is valid.

    Args:
        url: URL string

    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL.

    Args:
        url: URL string

    Returns:
        Domain name or None
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return None


def time_ago(dt: datetime) -> str:
    """Convert datetime to 'time ago' string.

    Args:
        dt: Datetime object

    Returns:
        Human-readable time ago string
    """
    now = datetime.utcnow()
    diff = now - dt

    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff < timedelta(days=30):
        days = diff.days
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif diff < timedelta(days=365):
        months = int(diff.days / 30)
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = int(diff.days / 365)
        return f"{years} year{'s' if years > 1 else ''} ago"


def chunk_text(text: str, max_length: int = 1000) -> List[str]:
    """Split text into chunks of maximum length.

    Args:
        text: Input text
        max_length: Maximum length per chunk

    Returns:
        List of text chunks
    """
    chunks = []
    words = text.split()
    current_chunk = []
    current_length = 0

    for word in words:
        word_length = len(word) + 1  # +1 for space
        if current_length + word_length > max_length:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, create if not.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_duration(seconds: int) -> str:
    """Format duration in seconds to HH:MM:SS.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length.

    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text (simple implementation).

    Args:
        text: Input text
        max_keywords: Maximum number of keywords

    Returns:
        List of keywords
    """
    # Remove common Japanese stop words and punctuation
    stop_words = {
        "の", "に", "は", "を", "た", "が", "で", "て", "と", "し", "れ", "さ",
        "ある", "いる", "も", "する", "から", "な", "こと", "として", "い",
        "や", "れる", "など", "なっ", "ない", "この", "ため", "その", "あっ",
        "よう", "また", "もの", "という", "あり", "まで", "られ", "なる",
    }

    # Simple word extraction (in real implementation, use morphological analysis)
    words = re.findall(r"\w+", text.lower())
    word_freq = {}

    for word in words:
        if len(word) > 1 and word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1

    # Sort by frequency
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:max_keywords]]
