"""Main video generation pipeline orchestrator."""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from src.core.config import get_settings
from src.core.logging import get_logger
from src.collectors.news_collector import NewsCollector
from src.analyzers.trend_analyzer import TrendAnalyzer
from src.generators.script_generator import ScriptGenerator
from src.voice.tts_generator import TTSGenerator
from src.video.visual_assets import VisualAssetsCollector
from src.video.editor import VideoEditor
from src.thumbnail.generator import ThumbnailGenerator
from src.seo.optimizer import SEOOptimizer
from src.quality.checker import QualityChecker
from src.utils.helpers import extract_keywords

logger = get_logger(__name__)
settings = get_settings()


class VideoGenerationPipeline:
    """Complete video generation pipeline."""

    def __init__(self) -> None:
        """Initialize pipeline with all components."""
        self.news_collector = NewsCollector()
        self.trend_analyzer = TrendAnalyzer()
        self.script_generator = ScriptGenerator()
        self.tts_generator = TTSGenerator()
        self.visual_collector = VisualAssetsCollector()
        self.video_editor = VideoEditor()
        self.thumbnail_generator = ThumbnailGenerator()
        self.seo_optimizer = SEOOptimizer()
        self.quality_checker = QualityChecker()

    async def generate_complete_video(
        self,
        topic: Optional[str] = None,
        category: str = "technology",
        auto_upload: bool = False,
    ) -> Dict:
        """Generate complete video from start to finish.

        Args:
            topic: Specific topic (if None, will analyze trends)
            category: Video category
            auto_upload: Whether to auto-upload to YouTube

        Returns:
            Dictionary with generation results
        """
        logger.info("=" * 60)
        logger.info("Starting complete video generation pipeline")
        logger.info("=" * 60)

        video_id = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = {
            "status": "in_progress",
            "video_id": video_id,
            "category": category,
        }

        try:
            # ========== STEP 1: Collect Information ==========
            logger.info("STEP 1/9: Collecting information...")

            if topic:
                articles = await self.news_collector.collect_from_newsapi(
                    query=topic,
                    category=category,
                    max_results=10,
                )
            else:
                # Collect tech news by default
                articles = await self.news_collector.collect_tech_news(max_results=20)

            if not articles:
                logger.error("No articles collected")
                result["status"] = "error"
                result["message"] = "No content found"
                return result

            logger.info(f"✓ Collected {len(articles)} articles")

            # ========== STEP 2: Analyze Trends & Select Topic ==========
            logger.info("STEP 2/9: Analyzing trends and selecting best topic...")

            scored_topics = await self.trend_analyzer.select_best_topics(
                articles=articles,
                category=category,
                max_topics=1,
            )

            if not scored_topics:
                logger.error("No suitable topics found")
                result["status"] = "error"
                result["message"] = "No suitable topics found"
                return result

            best_article, trend_score = scored_topics[0]
            logger.info(f"✓ Selected topic: {best_article.title}")
            logger.info(f"  Trend score: {trend_score.score:.2f}")

            # ========== STEP 3: Generate Script ==========
            logger.info("STEP 3/9: Generating video script...")

            # Combine related articles for richer content
            related_articles = [article for article, _ in scored_topics[:3]]
            combined_content = "\n\n".join([
                f"【{article.title}】\n{article.content}"
                for article in related_articles
            ])

            script = await self.script_generator.generate_script(
                topic=best_article.title,
                content=combined_content,
                target_duration=settings.default_video_length,
            )

            logger.info(f"✓ Script generated: {len(script.script)} characters")
            logger.info(f"  Title: {script.title}")

            result["title"] = script.title
            result["script"] = script.script
            result["raw_description"] = script.description
            result["raw_tags"] = script.tags

            # ========== STEP 4: Optimize SEO ==========
            logger.info("STEP 4/9: Optimizing SEO metadata...")

            keywords = extract_keywords(script.script, max_keywords=10)
            seo_metadata = await self.seo_optimizer.optimize_all_metadata(
                title=script.title,
                script=script.script,
                category=category,
                keywords=keywords,
            )

            logger.info(f"✓ SEO optimized")
            logger.info(f"  Optimized title: {seo_metadata['title']}")

            result["title"] = seo_metadata["title"]
            result["description"] = seo_metadata["description"]
            result["tags"] = seo_metadata["tags"]
            result["hashtags"] = seo_metadata["hashtags"]

            # ========== STEP 5: Generate Voice ==========
            logger.info("STEP 5/9: Generating voice narration...")

            try:
                audio_path = await self.tts_generator.generate_speech_for_script(
                    script=script.script,
                    video_id=video_id,
                )
                logger.info(f"✓ Voice generated: {audio_path}")
                result["audio_path"] = str(audio_path)
            except Exception as e:
                logger.warning(f"Voice generation failed: {e}")
                logger.warning("Continuing without audio (will use silent video)")
                audio_path = None

            # ========== STEP 6: Collect Visual Assets ==========
            logger.info("STEP 6/9: Collecting visual assets...")

            images = await self.visual_collector.collect_images_for_topic(
                topic=best_article.title,
                keywords=keywords[:5],
                count=5,
            )

            logger.info(f"✓ Collected {len(images)} images")
            result["images"] = [str(img) for img in images]

            # ========== STEP 7: Generate Video ==========
            logger.info("STEP 7/9: Generating video...")

            video_path = settings.video_output_path / f"{video_id}.mp4"

            if audio_path:
                video_path = await self.video_editor.create_simple_video(
                    images=images,
                    audio_path=audio_path,
                    output_path=video_path,
                    title=seo_metadata["title"],
                )
            else:
                # Create video without audio
                from src.video.editor import VideoScene
                scenes = [
                    VideoScene(image_path=img, duration=5.0)
                    for img in images
                ]
                video_path = await self.video_editor.create_video(
                    scenes=scenes,
                    audio_path=None,
                    output_path=video_path,
                    title=seo_metadata["title"],
                )

            logger.info(f"✓ Video generated: {video_path}")
            result["video_path"] = str(video_path)

            # ========== STEP 8: Generate Thumbnail ==========
            logger.info("STEP 8/9: Generating thumbnail...")

            thumbnail_path = settings.image_output_path / f"{video_id}_thumbnail.jpg"
            thumbnail = await self.thumbnail_generator.generate_thumbnail(
                text=script.thumbnail_text or seo_metadata["title"][:30],
                output_path=thumbnail_path,
                template="bold",
                background_image=images[0] if images else None,
            )

            logger.info(f"✓ Thumbnail generated: {thumbnail}")
            result["thumbnail_path"] = str(thumbnail)

            # ========== STEP 9: Quality Check ==========
            logger.info("STEP 9/9: Performing quality check...")

            source_urls = [article.url for article in related_articles]
            quality_result = await self.quality_checker.comprehensive_quality_check(
                title=seo_metadata["title"],
                description=seo_metadata["description"],
                script=script.script,
                tags=seo_metadata["tags"],
                video_path=video_path,
                sources=source_urls,
                recent_titles=[],  # TODO: Load from database
            )

            logger.info(f"✓ Quality check complete")
            if quality_result["overall_pass"]:
                logger.info("  ✓ All checks passed")
            else:
                logger.warning(f"  ✗ Issues found: {quality_result['errors']}")

            result["quality_check"] = quality_result

            # ========== FINAL STATUS ==========
            result["status"] = "success"
            logger.info("=" * 60)
            logger.info("✓ Video generation pipeline completed successfully!")
            logger.info("=" * 60)

            return result

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            result["status"] = "error"
            result["message"] = str(e)
            return result

    async def generate_batch_videos(
        self,
        count: int = 3,
        category: str = "technology",
    ) -> List[Dict]:
        """Generate multiple videos in batch.

        Args:
            count: Number of videos to generate
            category: Video category

        Returns:
            List of generation results
        """
        logger.info(f"Generating batch of {count} videos")

        results = []

        for i in range(count):
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Generating video {i+1}/{count}")
            logger.info(f"{'=' * 60}\n")

            result = await self.generate_complete_video(
                topic=None,
                category=category,
            )

            results.append(result)

            # Small delay between generations
            if i < count - 1:
                import asyncio
                await asyncio.sleep(10)

        successful = sum(1 for r in results if r.get("status") == "success")
        logger.info(f"\nBatch complete: {successful}/{count} videos generated successfully")

        return results
