"""Quality check system for video content."""

from pathlib import Path
from typing import List, Dict, Tuple
import re
from datetime import datetime, timedelta

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class QualityChecker:
    """Check video quality before publishing."""

    def __init__(self) -> None:
        """Initialize quality checker."""
        self.forbidden_keywords = settings.get_forbidden_keywords_list()
        self.min_video_duration = 270  # 4.5 minutes
        self.max_video_duration = 330  # 5.5 minutes
        self.min_resolution = (1280, 720)

    def check_forbidden_content(self, text: str) -> Tuple[bool, List[str]]:
        """Check for forbidden keywords in text.

        Args:
            text: Text to check

        Returns:
            Tuple of (is_clean, list_of_found_keywords)
        """
        found_keywords = []

        for keyword in self.forbidden_keywords:
            if keyword.lower() in text.lower():
                found_keywords.append(keyword)

        is_clean = len(found_keywords) == 0

        if not is_clean:
            logger.warning(f"Forbidden keywords found: {found_keywords}")

        return is_clean, found_keywords

    def check_duplicate_content(
        self,
        title: str,
        recent_titles: List[str],
        similarity_threshold: float = 0.7,
    ) -> Tuple[bool, List[str]]:
        """Check for duplicate or very similar content.

        Args:
            title: Title to check
            recent_titles: List of recent titles
            similarity_threshold: Similarity threshold

        Returns:
            Tuple of (is_unique, list_of_similar_titles)
        """
        similar_titles = []

        title_words = set(title.lower().split())

        for recent_title in recent_titles:
            recent_words = set(recent_title.lower().split())

            # Jaccard similarity
            intersection = len(title_words & recent_words)
            union = len(title_words | recent_words)

            if union > 0:
                similarity = intersection / union
                if similarity >= similarity_threshold:
                    similar_titles.append(recent_title)

        is_unique = len(similar_titles) == 0

        if not is_unique:
            logger.warning(f"Similar content found: {similar_titles}")

        return is_unique, similar_titles

    def check_video_duration(self, duration: int) -> Tuple[bool, str]:
        """Check if video duration is appropriate.

        Args:
            duration: Video duration in seconds

        Returns:
            Tuple of (is_valid, message)
        """
        if duration < self.min_video_duration:
            message = f"Video too short: {duration}s (min: {self.min_video_duration}s)"
            logger.warning(message)
            return False, message
        elif duration > self.max_video_duration:
            message = f"Video too long: {duration}s (max: {self.max_video_duration}s)"
            logger.warning(message)
            return False, message
        else:
            return True, "Duration OK"

    def check_video_file(self, video_path: Path) -> Tuple[bool, Dict]:
        """Check video file quality.

        Args:
            video_path: Path to video file

        Returns:
            Tuple of (is_valid, details_dict)
        """
        details = {
            "exists": False,
            "size_mb": 0,
            "resolution": None,
            "duration": 0,
            "issues": [],
        }

        # Check file exists
        if not video_path.exists():
            details["issues"].append("Video file not found")
            return False, details

        details["exists"] = True

        # Check file size
        file_size = video_path.stat().st_size
        size_mb = file_size / (1024 * 1024)
        details["size_mb"] = round(size_mb, 2)

        if size_mb < 1:
            details["issues"].append(f"File too small: {size_mb:.2f}MB")
        elif size_mb > 500:
            details["issues"].append(f"File too large: {size_mb:.2f}MB")

        # Try to get video properties using ffprobe (if available)
        try:
            import ffmpeg
            probe = ffmpeg.probe(str(video_path))

            # Get video stream
            video_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'video'),
                None
            )

            if video_stream:
                width = int(video_stream['width'])
                height = int(video_stream['height'])
                details["resolution"] = (width, height)

                # Check resolution
                if width < self.min_resolution[0] or height < self.min_resolution[1]:
                    details["issues"].append(
                        f"Resolution too low: {width}x{height} "
                        f"(min: {self.min_resolution[0]}x{self.min_resolution[1]})"
                    )

            # Get duration
            if 'duration' in probe['format']:
                duration = float(probe['format']['duration'])
                details["duration"] = int(duration)

                # Check duration
                is_valid, message = self.check_video_duration(int(duration))
                if not is_valid:
                    details["issues"].append(message)

        except Exception as e:
            logger.warning(f"Could not probe video file: {e}")
            details["issues"].append("Could not verify video properties")

        is_valid = len(details["issues"]) == 0

        return is_valid, details

    def check_copyright(self, content: str, sources: List[str]) -> Tuple[bool, List[str]]:
        """Check for potential copyright issues.

        Args:
            content: Content text
            sources: List of source URLs

        Returns:
            Tuple of (is_clear, list_of_issues)
        """
        issues = []

        # Check for copyrighted phrases (simple heuristic)
        copyright_patterns = [
            r'©\s*\d{4}',
            r'copyright\s+\d{4}',
            r'all rights reserved',
            r'著作権',
        ]

        for pattern in copyright_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"Potential copyright notice found: {pattern}")

        # Check source diversity (avoid relying on single source)
        if len(sources) < 2:
            issues.append("Content from only one source - consider diversifying")

        # Check for direct quotes (should be attributed)
        quote_pattern = r'「.{50,}」'
        quotes = re.findall(quote_pattern, content)
        if len(quotes) > 3:
            issues.append(f"Many long quotes found ({len(quotes)}) - ensure proper attribution")

        is_clear = len(issues) == 0

        if issues:
            logger.warning(f"Copyright issues: {issues}")

        return is_clear, issues

    def check_spam_signals(
        self,
        title: str,
        description: str,
        tags: List[str],
    ) -> Tuple[bool, List[str]]:
        """Check for spam signals that might trigger YouTube filters.

        Args:
            title: Video title
            description: Video description
            tags: Video tags

        Returns:
            Tuple of (is_clean, list_of_issues)
        """
        issues = []

        # Check for excessive capitalization
        if title.isupper() and len(title) > 10:
            issues.append("Title is all caps")

        # Check for excessive exclamation marks
        if title.count('!') > 3 or title.count('！') > 3:
            issues.append("Excessive exclamation marks in title")

        # Check for keyword stuffing in description
        words = description.lower().split()
        if len(words) > 50:
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Ignore short words
                    word_freq[word] = word_freq.get(word, 0) + 1

            # Check if any word appears too frequently
            max_freq = max(word_freq.values()) if word_freq else 0
            if max_freq > len(words) * 0.05:  # More than 5% of total words
                issues.append("Potential keyword stuffing detected")

        # Check for too many tags
        if len(tags) > 30:
            issues.append(f"Too many tags: {len(tags)} (recommended: 10-15)")

        # Check for duplicate tags
        if len(tags) != len(set(tags)):
            issues.append("Duplicate tags found")

        is_clean = len(issues) == 0

        if issues:
            logger.warning(f"Spam signals detected: {issues}")

        return is_clean, issues

    async def comprehensive_quality_check(
        self,
        title: str,
        description: str,
        script: str,
        tags: List[str],
        video_path: Path,
        sources: List[str],
        recent_titles: List[str],
    ) -> Dict[str, any]:
        """Perform comprehensive quality check on video.

        Args:
            title: Video title
            description: Video description
            script: Video script
            tags: Video tags
            video_path: Path to video file
            sources: Source URLs
            recent_titles: Recent video titles

        Returns:
            Dictionary with check results
        """
        logger.info("Starting comprehensive quality check")

        results = {
            "overall_pass": False,
            "checks": {},
            "warnings": [],
            "errors": [],
        }

        # 1. Check forbidden content
        content_clean, forbidden = self.check_forbidden_content(title + " " + script)
        results["checks"]["forbidden_content"] = {
            "pass": content_clean,
            "issues": forbidden,
        }
        if not content_clean:
            results["errors"].append(f"Forbidden keywords found: {forbidden}")

        # 2. Check duplicate content
        is_unique, similar = self.check_duplicate_content(title, recent_titles)
        results["checks"]["duplicate_content"] = {
            "pass": is_unique,
            "similar_titles": similar,
        }
        if not is_unique:
            results["warnings"].append(f"Similar content exists: {similar}")

        # 3. Check video file
        file_valid, file_details = self.check_video_file(video_path)
        results["checks"]["video_file"] = {
            "pass": file_valid,
            "details": file_details,
        }
        if not file_valid:
            results["errors"].extend(file_details["issues"])

        # 4. Check copyright
        copyright_clear, copyright_issues = self.check_copyright(script, sources)
        results["checks"]["copyright"] = {
            "pass": copyright_clear,
            "issues": copyright_issues,
        }
        if not copyright_clear:
            results["warnings"].extend(copyright_issues)

        # 5. Check spam signals
        spam_clean, spam_issues = self.check_spam_signals(title, description, tags)
        results["checks"]["spam"] = {
            "pass": spam_clean,
            "issues": spam_issues,
        }
        if not spam_clean:
            results["warnings"].extend(spam_issues)

        # Determine overall pass/fail
        # Fail if any errors (not just warnings)
        results["overall_pass"] = len(results["errors"]) == 0

        if results["overall_pass"]:
            logger.info("✓ Quality check passed")
        else:
            logger.warning(f"✗ Quality check failed: {results['errors']}")

        return results
