"""
Main entry point for the foodScrapper application.
Example usage of different scrapers.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import config
from foodpanda.scrapers.v1Scraper import FoodPandaV1Scraper
from foodpanda.scrapers.v2Scraper import FoodPandaV2Scraper
from foodi.scrapers.v1Scraper import FoodiV1Scraper
from foodi.scrapers.v2Scraper import FoodiV2Scraper
from utils.helpers import format_filename, save_json, setup_logging


# Setup logging
setup_logging(log_level=config.scraper.LOG_LEVEL)
logger = logging.getLogger(__name__)


async def scrape_foodpanda_v1() -> None:
    """Example: Scrape FoodPanda using v1 scraper."""
    logger.info("Starting FoodPanda V1 scraper...")

    try:
        scraper = FoodPandaV1Scraper(
            headless=config.scraper.HEADLESS,
            use_stealth=config.scraper.USE_STEALTH,
        )

        async with scraper:
            result = await scraper.scrape()

        # Save results
        filename = format_filename("foodpanda_v1")
        output_path = Path("output") / filename
        save_json(result, str(output_path))

        logger.info(f"FoodPanda V1 scraping completed. Found {result.get('count', 0)} restaurants.")

    except Exception as e:
        logger.error(f"FoodPanda V1 scraping failed: {str(e)}")



async def main() -> None:
    """Main entry point."""
    logger.info("foodScrapper application started")

    # Example: Run a single scraper
    # await scrape_foodpanda_v1()

    # Example: Run all scrapers
    # await asyncio.gather(
    #     scrape_foodpanda_v1(),
    #     scrape_foodpanda_v2(),
    #     scrape_foodi_v1(),
    #     scrape_foodi_v2(),
    # )

    logger.info("foodScrapper application finished")


if __name__ == "__main__":
    asyncio.run(main())
