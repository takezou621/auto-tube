#!/usr/bin/env python
"""Basic functionality test without external APIs."""

import sys
sys.path.insert(0, '/home/user/auto-tube')

def test_imports():
    """Test basic module imports."""
    print("=" * 60)
    print("AUTO-TUBE BASIC FUNCTIONALITY TEST")
    print("=" * 60)

    print("\n1. Testing Core Modules...")
    try:
        from src.core.config import get_settings
        settings = get_settings()
        print(f"   ✓ Config: {settings.app_name}")

        from src.core.logging import setup_logging, get_logger
        print("   ✓ Logging module")

        from src.utils.helpers import sanitize_filename, format_duration, extract_keywords
        print("   ✓ Helper functions")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    print("\n2. Testing Helper Functions...")
    try:
        # Sanitize filename
        test_name = "Test Video: AI & ML Technology!"
        clean_name = sanitize_filename(test_name)
        print(f"   ✓ Sanitize: \"{test_name[:30]}...\" -> \"{clean_name[:30]}...\"")

        # Format duration
        duration_str = format_duration(305)
        print(f"   ✓ Format duration: 305s -> {duration_str}")

        # Extract keywords
        text = "人工知能 AI 機械学習 テクノロジー ニュース まとめ 最新"
        keywords = extract_keywords(text, max_keywords=5)
        print(f"   ✓ Extract keywords: {keywords[:5]}")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    print("\n3. Testing Data Structures...")
    try:
        from datetime import datetime

        # Test without importing modules that need external deps
        print("   ✓ DateTime module")
        print(f"   ✓ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    print("\n4. Testing Configuration...")
    try:
        print(f"   ✓ App name: {settings.app_name}")
        print(f"   ✓ Video length: {settings.default_video_length}s")
        print(f"   ✓ Video resolution: {settings.video_resolution}")
        print(f"   ✓ Language: {settings.default_language}")
        print(f"   ✓ Category: {settings.default_category}")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    print("\n5. Testing File Paths...")
    try:
        from pathlib import Path
        print(f"   ✓ Video output: {settings.video_output_path}")
        print(f"   ✓ Audio output: {settings.audio_output_path}")
        print(f"   ✓ Image output: {settings.image_output_path}")

        # Check if directories exist
        if settings.video_output_path.exists():
            print("   ✓ Video directory exists")
        if settings.audio_output_path.exists():
            print("   ✓ Audio directory exists")
        if settings.image_output_path.exists():
            print("   ✓ Image directory exists")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    return True


def test_thumbnail_generation():
    """Test thumbnail generation without external APIs."""
    print("\n6. Testing Thumbnail Generation...")
    try:
        from src.thumbnail.generator import ThumbnailGenerator
        from pathlib import Path

        generator = ThumbnailGenerator()
        print("   ✓ ThumbnailGenerator initialized")
        print(f"   ✓ Available templates: {generator.templates}")
        print(f"   ✓ Thumbnail size: {generator.width}x{generator.height}")

        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_seo_optimizer():
    """Test SEO optimizer structure."""
    print("\n7. Testing SEO Optimizer...")
    try:
        from src.seo.optimizer import SEOOptimizer

        print("   ✓ SEOOptimizer class available")
        print("   ⚠ Note: Actual optimization requires OpenAI API key")

        return True
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


def main():
    """Run all tests."""
    results = []

    results.append(("Basic Imports", test_imports()))
    results.append(("Thumbnail Generator", test_thumbnail_generation()))
    results.append(("SEO Optimizer", test_seo_optimizer()))

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All basic tests passed!")
        print("\nNext steps:")
        print("1. Set up API keys in .env file")
        print("2. Install remaining dependencies")
        print("3. Run full integration test")
    else:
        print("\n⚠ Some tests failed. Check errors above.")

    print("=" * 60)


if __name__ == "__main__":
    main()
