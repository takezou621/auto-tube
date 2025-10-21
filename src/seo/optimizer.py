"""SEO optimization module for YouTube videos."""

from typing import List, Dict
import re

from openai import AsyncOpenAI

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SEOOptimizer:
    """Optimize video metadata for YouTube SEO."""

    def __init__(self) -> None:
        """Initialize SEO optimizer."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def optimize_title(
        self,
        title: str,
        keywords: List[str],
        max_length: int = 60,
    ) -> str:
        """Optimize video title for SEO and CTR.

        Args:
            title: Original title
            keywords: Target keywords
            max_length: Maximum title length

        Returns:
            Optimized title
        """
        try:
            keywords_str = ", ".join(keywords[:5])

            prompt = f"""以下のYouTube動画タイトルをSEOとクリック率向上のために最適化してください。

元のタイトル: {title}
キーワード: {keywords_str}

最適化の要件:
1. {max_length}文字以内
2. 重要なキーワードを前方に配置
3. 数字や記号を効果的に使用（【】、！、？など）
4. クリックしたくなる表現
5. 誇張しすぎない（クリックベイト回避）
6. 日本語で自然な表現

最適化されたタイトルのみを返してください（説明不要）。
"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )

            optimized_title = response.choices[0].message.content.strip()

            # Ensure length limit
            if len(optimized_title) > max_length:
                optimized_title = optimized_title[:max_length-3] + "..."

            logger.info(f"Optimized title: '{title}' -> '{optimized_title}'")
            return optimized_title

        except Exception as e:
            logger.error(f"Error optimizing title: {e}")
            return title  # Return original on error

    async def generate_description(
        self,
        title: str,
        script: str,
        keywords: List[str],
        max_length: int = 5000,
    ) -> str:
        """Generate SEO-optimized video description.

        Args:
            title: Video title
            script: Video script
            keywords: Target keywords
            max_length: Maximum description length

        Returns:
            Optimized description
        """
        try:
            keywords_str = ", ".join(keywords[:10])
            script_preview = script[:500]

            prompt = f"""YouTube動画の説明文を作成してください。

タイトル: {title}
内容の概要: {script_preview}...
キーワード: {keywords_str}

要件:
1. 最初の150文字が特に重要（検索結果に表示される）
2. キーワードを自然に含める
3. 視聴者に価値を伝える
4. タイムスタンプを含める（例: 0:00 イントロ、0:30 本編開始）
5. 関連リンクやハッシュタグを含める
6. チャンネル登録を促す
7. {max_length}文字以内

説明文を返してください。
"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )

            description = response.choices[0].message.content.strip()

            # Ensure length limit
            if len(description) > max_length:
                description = description[:max_length]

            logger.info(f"Generated description: {len(description)} characters")
            return description

        except Exception as e:
            logger.error(f"Error generating description: {e}")
            # Fallback to simple description
            return f"{title}\n\n{script[:300]}...\n\n#YouTube #動画"

    async def generate_tags(
        self,
        title: str,
        content: str,
        category: str,
        max_tags: int = 15,
    ) -> List[str]:
        """Generate optimized tags for video.

        Args:
            title: Video title
            content: Video content/script
            category: Video category
            max_tags: Maximum number of tags

        Returns:
            List of tags
        """
        try:
            content_preview = content[:500]

            prompt = f"""YouTube動画のタグを生成してください。

タイトル: {title}
カテゴリ: {category}
内容: {content_preview}...

要件:
1. {max_tags}個のタグ
2. 幅広いタグ（一般的）と狭いタグ（特化）を混在
3. 競合チャンネルが使いそうなタグ
4. ロングテールキーワードを含める
5. 日本語と英語を混在させる

タグのみをカンマ区切りで返してください（説明不要）。
"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )

            tags_str = response.choices[0].message.content.strip()

            # Parse tags
            tags = [tag.strip() for tag in tags_str.split(",")]

            # Remove duplicates and limit
            tags = list(dict.fromkeys(tags))[:max_tags]

            logger.info(f"Generated {len(tags)} tags")
            return tags

        except Exception as e:
            logger.error(f"Error generating tags: {e}")
            # Fallback to basic tags
            return [category, "日本語", "解説", "まとめ", "ニュース"]

    async def generate_hashtags(
        self,
        title: str,
        keywords: List[str],
        max_hashtags: int = 3,
    ) -> List[str]:
        """Generate hashtags for video.

        Args:
            title: Video title
            keywords: Keywords
            max_hashtags: Maximum number of hashtags

        Returns:
            List of hashtags (with # prefix)
        """
        # Select top keywords
        hashtags = []

        for keyword in keywords[:max_hashtags]:
            # Clean keyword (remove spaces, special chars)
            clean_keyword = re.sub(r'[^\w]', '', keyword)
            if clean_keyword:
                hashtags.append(f"#{clean_keyword}")

        # Add category hashtag
        if len(hashtags) < max_hashtags:
            hashtags.append("#YouTube")

        logger.info(f"Generated hashtags: {hashtags}")
        return hashtags[:max_hashtags]

    async def optimize_all_metadata(
        self,
        title: str,
        script: str,
        category: str,
        keywords: List[str],
    ) -> Dict[str, any]:
        """Optimize all video metadata.

        Args:
            title: Original title
            script: Video script
            category: Video category
            keywords: Target keywords

        Returns:
            Dictionary with optimized metadata
        """
        logger.info("Optimizing all video metadata")

        # Optimize title
        optimized_title = await self.optimize_title(title, keywords)

        # Generate description
        description = await self.generate_description(
            optimized_title, script, keywords
        )

        # Generate tags
        tags = await self.generate_tags(optimized_title, script, category)

        # Generate hashtags
        hashtags = await self.generate_hashtags(optimized_title, keywords)

        metadata = {
            "title": optimized_title,
            "description": description,
            "tags": tags,
            "hashtags": hashtags,
            "category": category,
        }

        logger.info("Metadata optimization complete")
        return metadata

    def analyze_title_quality(self, title: str) -> Dict[str, any]:
        """Analyze title quality and provide recommendations.

        Args:
            title: Video title

        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "length": len(title),
            "has_numbers": bool(re.search(r'\d', title)),
            "has_brackets": bool(re.search(r'[【】\[\]]', title)),
            "has_punctuation": bool(re.search(r'[!?！？]', title)),
            "score": 0.0,
            "recommendations": [],
        }

        score = 0.0

        # Length check
        if 40 <= analysis["length"] <= 60:
            score += 0.3
        else:
            analysis["recommendations"].append(
                f"タイトルの長さを40-60文字に調整（現在: {analysis['length']}文字）"
            )

        # Numbers increase CTR
        if analysis["has_numbers"]:
            score += 0.2
        else:
            analysis["recommendations"].append("数字を含めるとCTRが向上します")

        # Brackets for emphasis
        if analysis["has_brackets"]:
            score += 0.2
        else:
            analysis["recommendations"].append("【】などの記号で重要部分を強調")

        # Punctuation for emotion
        if analysis["has_punctuation"]:
            score += 0.15
        else:
            analysis["recommendations"].append("！や？で感情を表現")

        # Keyword position (simple check - first 20 chars)
        first_part = title[:20]
        if len(first_part) > 5:
            score += 0.15

        analysis["score"] = score

        return analysis
