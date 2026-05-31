"""
Configuration Module

Centralized configuration for all scrapers with sensible defaults
and support for environment variable overrides.
"""

import os
import json
from typing import List, Optional


class ScraperConfig:
    """
    Configuration class for web scrapers.

    All settings can be overridden via environment variables.
    """

    # Browser settings
    headless: bool = os.getenv("HEADLESS", "true").lower() == "true"
    timeout: int = int(os.getenv("TIMEOUT", 5000))  # milliseconds
    navigation_timeout: int = int(os.getenv("NAVIGATION_TIMEOUT", 15000))

    # Retry settings
    max_retries: int = int(os.getenv("MAX_RETRIES", 3))
    retry_delay: float = float(os.getenv("RETRY_DELAY", 2.0))  # Base delay in seconds

    # Browser launch arguments
    browser_args: List[str] = [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",  # Disable shared memory (useful in Docker)
        "--disable-setuid-sandbox",
        "--no-sandbox",
        "--disable-web-security",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=IsolateOrigins,site-per-process",
    ]

    # Browser context settings
    viewport: Optional[dict] = {
        "width": 1470,
        "height": 956,
    }

    user_agent: str =(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/145.0.0.0 Safari/537.36"
            )

    locale: str = "en_BD"
    timezone: str = "Asia/Dhaka"
    permissions: List[str] = ["geolocation"]
    extra_http_headers: List[dict] = {
        "Accept-Language": "en-GB,en;q=0.9"
    }

    # Logging settings
    log_level: str = os.getenv("LOG_LEVEL", "DEBUG")
    log_file: str = os.getenv("LOG_FILE", "logs/scraper.log")

    # Data export settings
    export_format: str = os.getenv("EXPORT_FORMAT", "json")  # json or csv
    output_dir: str = os.getenv("OUTPUT_DIR", "output")

    # Website-specific delays
    request_delay: float = float(os.getenv("REQUEST_DELAY", 1.0))  # Delay between requests
    page_load_delay: float = float(os.getenv("PAGE_LOAD_DELAY", 2.0))

    @classmethod
    def to_dict(cls) -> dict:
        """Convert config to dictionary."""
        return {
            k: v for k, v in cls.__dict__.items()
            if not k.startswith('_') and not callable(v)
        }

    @classmethod
    def from_env(cls):
        """Load configuration from environment variables."""
        config = cls()
        # Config attributes are class variables, so modifications affect the class
        return config


# Website-specific configurations can be created by extending this class

class FoodPandaConfig(ScraperConfig):
    """FoodPanda specific configuration."""
    base_url: str = "https://www.foodpanda.com"
    request_delay: float = 2.0  # Be respectful to FoodPanda


class FoodiConfig(ScraperConfig):
    """Foodi specific configuration."""
    base_url: str = "https://www.foodi.com"
    request_delay: float = 1.5
    storage_data = {
        "foodi:devId": "0182c45e35ead912d3e3f05f-Brave, Chrome, Chromium, Not:A-Brand",
        # "formatted_address": "Road No. 5 & Sahid Zia College Road, Dhaka, Bangladesh",
        # "latitude": "23.823402040410024",
        # "longitude": "90.37264433488772",
        "navItems": json.dumps({
            "delivery": True,
            "pickup": False,
            "flower": False
        }),
        # "vertical": json.dumps({
        #     "id": 7,
        #     "name": "Food",
        #     "offerText": None,
        #     "offerBgColor": None,
        #     "offerTextColor": None,
        #     "pageType": 1,
        #     "platformType": 1,
        #     "verticalType": 2,
        #     "defaultServiceType": 1,
        #     "verticalForRedisServiceType": [
        #         {
        #             "level": "Delivery",
        #             "value": "isDelivery",
        #             "isActive": True,
        #             "isDefault": True
        #         },
        #         {
        #             "level": "Pickup",
        #             "value": "isPickup",
        #             "isActive": True,
        #             "isDefault": False
        #         }
        #     ],
        #     "sortOrder": 1,
        #     "sloganText": None,
        #     "sloganTextColor": None,
        #     "cardTextColor": None,
        #     "cardBgColor": None,
        #     "isDelivery": True,
        #     "isPickup": True,
        #     "isDine": False,
        #     "isFlower": False,
        #     "verticalTags": [1],
        #     "hints": [],
        #     "image": None,
        #     "isShowSingleBranchDetails": False,
        #     "slug": None
        # }),
        # "zoneId": "4"
    }