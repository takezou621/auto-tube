"""Script generation module using LLM."""

from typing import Dict, List
from dataclasses import dataclass

from openai import AsyncOpenAI

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class VideoScript:
    """Video script data structure."""

    title: str
    script: str
    description: str
    tags: List[str]
    thumbnail_text: str
    estimated_duration: int  # in seconds


class ScriptGenerator:
    """Generate video scripts using LLM."""

    def __init__(self) -> None:
        """Initialize script generator."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def generate_script(
        self,
        topic: str,
        content: str,
        target_duration: int = 300,
        language: str = "ja",
    ) -> VideoScript:
        """Generate video script from content.

        Args:
            topic: Video topic/theme
            content: Source content
            target_duration: Target duration in seconds
            language: Script language

        Returns:
            Generated video script
        """
        try:
            # Calculate approximate word count for target duration
            # Japanese: ~300 characters per minute
            # 5 minutes = ~1500 characters
            target_chars = int(target_duration / 60 * 300)

            system_prompt = """あなたはYouTube動画の台本作成の専門家です。
視聴者を引き込む魅力的な動画台本を作成してください。

以下のルールに従ってください:
1. 冒頭で視聴者の注目を引く
2. 情報をわかりやすく、簡潔に説明する
3. 専門用語は噛み砕いて説明する
4. 視聴者の興味を維持する構成にする
5. 最後にチャンネル登録を促す
6. 客観的で正確な情報を提供する
7. 炎上リスクのある表現を避ける
"""

            user_prompt = f"""以下の情報を基に、{target_duration}秒（約{target_duration//60}分）のYouTube動画の台本を作成してください。

トピック: {topic}

ソースコンテンツ:
{content[:4000]}  # Limit content length

要件:
- 台本の文字数: 約{target_chars}文字
- 言語: {language}
- 構成: オープニング、メインコンテンツ（3-5ポイント）、クロージング

以下のJSON形式で出力してください:
{{
  "title": "魅力的なタイトル（60文字以内）",
  "script": "完全な台本（オープニング、メイン、クロージングを含む）",
  "description": "動画の説明文（200文字程度、SEO最適化）",
  "tags": ["タグ1", "タグ2", "タグ3", ...],
  "thumbnail_text": "サムネイル用の短いテキスト（10文字以内）"
}}
"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            result = response.choices[0].message.content
            import json
            script_data = json.loads(result)

            # Estimate duration (assuming ~5 chars per second for Japanese speech)
            estimated_duration = len(script_data["script"]) // 5

            video_script = VideoScript(
                title=script_data.get("title", topic),
                script=script_data.get("script", ""),
                description=script_data.get("description", ""),
                tags=script_data.get("tags", []),
                thumbnail_text=script_data.get("thumbnail_text", ""),
                estimated_duration=estimated_duration,
            )

            logger.info(f"Generated script for topic: {topic}")
            return video_script

        except Exception as e:
            logger.error(f"Error generating script: {e}")
            raise

    async def optimize_title(self, title: str) -> str:
        """Optimize title for SEO and click-through rate.

        Args:
            title: Original title

        Returns:
            Optimized title
        """
        try:
            prompt = f"""以下のYouTube動画タイトルをSEOとクリック率向上のために最適化してください。

元のタイトル: {title}

要件:
- 60文字以内
- キーワードを前方に配置
- 数字や記号を効果的に使用（【】、！、？など）
- クリックしたくなる表現
- 誇張しすぎない（クリックベイト回避）

最適化されたタイトルのみを返してください。
"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )

            optimized_title = response.choices[0].message.content.strip()
            logger.info(f"Optimized title: {title} -> {optimized_title}")
            return optimized_title

        except Exception as e:
            logger.error(f"Error optimizing title: {e}")
            return title  # Return original on error
