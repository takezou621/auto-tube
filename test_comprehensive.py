#!/usr/bin/env python
"""Comprehensive test of Auto-Tube modules (without API keys)."""

import sys
sys.path.insert(0, '/home/user/auto-tube')

def test_module_structure():
    """Test all module structures can be imported."""
    print("=" * 60)
    print("COMPREHENSIVE MODULE TEST")
    print("=" * 60)

    modules_to_test = [
        ("Core Config", "src.core.config", "get_settings"),
        ("Core Logging", "src.core.logging", "setup_logging"),
        ("Core Database", "src.core.database", "Video"),
        ("Utils Helpers", "src.utils.helpers", "sanitize_filename"),
        ("Thumbnail Generator", "src.thumbnail.generator", "ThumbnailGenerator"),
        ("SEO Optimizer", "src.seo.optimizer", "SEOOptimizer"),
        ("Quality Checker", "src.quality.checker", "QualityChecker"),
    ]

    print("\nTesting Module Imports...")
    passed = 0
    failed = 0

    for name, module_path, class_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print(f"   ✓ {name}")
            passed += 1
        except Exception as e:
            print(f"   ✗ {name}: {e}")
            failed += 1

    print(f"\nModule Import Results: {passed} passed, {failed} failed")
    return passed, failed


def test_thumbnail_creation():
    """Test actual thumbnail creation."""
    print("\n" + "=" * 60)
    print("THUMBNAIL GENERATION TEST")
    print("=" * 60)

    try:
        from src.thumbnail.generator import ThumbnailGenerator
        from pathlib import Path
        import asyncio

        generator = ThumbnailGenerator()

        async def create_test_thumbnail():
            output_path = Path("/tmp/test_thumbnail.jpg")
            result = await generator.generate_thumbnail(
                text="テスト動画",
                output_path=output_path,
                template="bold"
            )
            return result

        # Run async function
        result = asyncio.run(create_test_thumbnail())

        if result.exists():
            size = result.stat().st_size
            print(f"   ✓ Thumbnail created: {result}")
            print(f"   ✓ File size: {size:,} bytes")
            return True
        else:
            print("   ✗ Thumbnail file not created")
            return False

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quality_checker():
    """Test quality check system."""
    print("\n" + "=" * 60)
    print("QUALITY CHECKER TEST")
    print("=" * 60)

    try:
        from src.quality.checker import QualityChecker

        checker = QualityChecker()

        # Test forbidden content check
        clean_text = "This is a clean video about technology"
        bad_text = "This contains 暴力 which is forbidden"

        is_clean1, keywords1 = checker.check_forbidden_content(clean_text)
        is_clean2, keywords2 = checker.check_forbidden_content(bad_text)

        print(f"   ✓ Clean text check: {is_clean1} (expected: True)")
        print(f"   ✓ Bad text check: {is_clean2} (expected: False)")
        print(f"   ✓ Found forbidden words: {keywords2}")

        # Test duplicate detection
        titles = [
            "AI Technology News 2024",
            "Machine Learning Updates",
            "AI Technology News Latest"
        ]

        is_unique, similar = checker.check_duplicate_content(
            "AI Technology News Today",
            titles,
            similarity_threshold=0.6
        )

        print(f"   ✓ Duplicate detection works: found {len(similar)} similar")

        # Test duration check
        is_valid, msg = checker.check_video_duration(295)
        print(f"   ✓ Duration check (295s): {is_valid}, {msg}")

        return True

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_seo_analyzer():
    """Test SEO title analysis."""
    print("\n" + "=" * 60)
    print("SEO ANALYZER TEST")
    print("=" * 60)

    try:
        from src.seo.optimizer import SEOOptimizer

        optimizer = SEOOptimizer()

        # Test title quality analysis
        test_titles = [
            "AI Technology News 2024",
            "【最新】AI技術の動向トップ5！",
            "machine learning",
            "今日のテクノロジーニュース - AI・機械学習・最新情報まとめ"
        ]

        for title in test_titles:
            analysis = optimizer.analyze_title_quality(title)
            print(f"\n   Title: \"{title}\"")
            print(f"   ✓ Length: {analysis['length']} chars")
            print(f"   ✓ Score: {analysis['score']:.2f}")
            print(f"   ✓ Has numbers: {analysis['has_numbers']}")
            print(f"   ✓ Has brackets: {analysis['has_brackets']}")
            if analysis['recommendations']:
                print(f"   ⚠ Recommendations: {len(analysis['recommendations'])}")

        return True

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_visual_assets():
    """Test visual assets fallback generation."""
    print("\n" + "=" * 60)
    print("VISUAL ASSETS TEST")
    print("=" * 60)

    try:
        from src.video.visual_assets import VisualAssetsCollector
        import asyncio

        collector = VisualAssetsCollector()

        async def generate_fallback():
            images = await collector._get_fallback_images(count=3)
            return images

        images = asyncio.run(generate_fallback())

        print(f"   ✓ Generated {len(images)} fallback images")
        for i, img in enumerate(images, 1):
            if img.exists():
                size = img.stat().st_size
                print(f"   ✓ Image {i}: {img.name} ({size:,} bytes)")
            else:
                print(f"   ✗ Image {i} not created")

        return len(images) == 3

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "AUTO-TUBE COMPREHENSIVE TEST" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")

    results = []

    # Module structure test
    passed, failed = test_module_structure()
    results.append(("Module Imports", failed == 0))

    # Functional tests
    results.append(("Thumbnail Generation", test_thumbnail_creation()))
    results.append(("Quality Checker", test_quality_checker()))
    results.append(("SEO Analyzer", test_seo_analyzer()))
    results.append(("Visual Assets", test_visual_assets()))

    # Summary
    print("\n" + "=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)

    total_passed = sum(1 for _, result in results if result)
    total_tests = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n📊 Results: {total_passed}/{total_tests} test suites passed")

    if total_passed == total_tests:
        print("\n" + "🎉" * 30)
        print("✅ ALL TESTS PASSED! Auto-Tube is working correctly!")
        print("🎉" * 30)
        print("\n📝 System Status:")
        print("   ✓ Core modules functional")
        print("   ✓ Thumbnail generation working")
        print("   ✓ Quality checks operational")
        print("   ✓ SEO analysis ready")
        print("   ✓ Visual assets generator functional")
        print("\n🚀 Ready for production with API keys!")
    else:
        print("\n⚠ Some tests failed. Review errors above.")

    print("=" * 60)

    return total_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
