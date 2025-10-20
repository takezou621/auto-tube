#!/usr/bin/env python
"""Initialize database tables."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import init_db
from src.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def main() -> None:
    """Initialize database."""
    logger.info("Initializing database...")
    try:
        await init_db()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
