# scrapers/foodi/v1Scrapper.py

"""
Foodi v1 Scraper

Version 1: Basic implementation for scraping restaurants from Foodi.

This version includes:
- Restaurant listing extraction

"""

import asyncio
import base64
import csv
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import time
from tqdm import tqdm

import pandas as pd
from playwright.async_api import Page, Locator
from scrapers.baseScraper import BaseScraper
from utils.config import FoodiConfig
from utils.logger import get_logger
from utils.validators import clean_price, clean_rating, clean_text


class FoodiV1Scraper(BaseScraper):
    """
    Foodi v1 Scraper - With proper API headers.

    This scraper handles:
    - Location-based restaurant filtering

    Example usage:
    ```python
    async def main():
        scraper = FoodiV1Scraper()
        scraper.set_location(latitude=23.8103, longitude=90.4125)
        data = await scraper.run()
        print(f"Scraped {len(data)} restaurants")

    asyncio.run(main())
    ```
    """

    def __init__(self):
        """Initialize Foodi v1 scraper."""
        super().__init__(
            website_name="foodi",
            version="v1"
        )
        
        # Headers cache
        self._context_headers = None
        self._logger = get_logger(f"{self.website_name}_{self.version}")
        self.foodi_init_scripts = FoodiConfig().storage_data

    async def setup_scraper(self) -> None:
        """
        Setup browser with FoodPanda-specific headers.

        Configures:
        - Context-level headers (apply to all requests)
        - Request interception for dynamic headers
        - Session tracking IDs
        """

        # pass website wise context level extra http headers
        await self.setup_browser(init_scripts = self.foodi_init_scripts)

    def _get_context_headers(self) -> Dict[str, str]:
        """
        Get headers that apply to all requests from this page.

        These headers are set once and apply to every request from the browser.
        They include browser identification, accepted content types, and CORS headers.

        Returns:
            Dictionary of context-level headers
        """
        if self._context_headers:
            return self._context_headers

        self._context_headers = {
            # Content negotiation
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-GB,en;q=0.9",
            
            # CORS and Origin
            # "origin": self.WEB_URL,
            # "referer": f"{self.WEB_URL}/",
            
            # Security headers (Fetch Metadata)
            "sec-ch-ua": '"Not:A-Brand";v="99", "Chromium";v="145"',
            # "sec-ch-ua-mobile": "?0",
            # "sec-ch-ua-platform": '"Windows"',
            # "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "sec-gpc": "1",
        }
        
        return self._context_headers

    async def load_all_restaurants(self):
        """
        Load all restaurants by scrolling through infinite scroll pagination.
        
        Strategy:
        1. Get initial restaurant count
        2. Scroll to bottom (triggers loading more)
        3. Wait for page to load (networkidle)
        4. Count restaurants again
        5. If count increased: repeat step 2
        6. If count unchanged: all restaurants loaded
        
        Returns:
            Total elements of restaurants loaded
        """
        self.logger.info("Loading all restaurants via infinite scroll...")
        max_retries = 50  # Max scroll attempts
        retry_count = 0
        previous_count = 0
        restaurants = None

        while retry_count < max_retries:
            # Get current restaurant count
            all_restaurants_section = self._page.locator("//h5[text()='All Restaurants']/parent::div") #used xpath axes
            await all_restaurants_section.scroll_into_view_if_needed(timeout=10000)
            restaurants = all_restaurants_section.locator("div.restaurant-item-card")
            await self._page.pause()
            current_count = await restaurants.count()
            print("current count", current_count)
            
            self.logger.info(f"Scroll attempt {retry_count + 1}: Found {current_count} restaurants")
            
            # Check if count increased
            if current_count == previous_count:
                self.logger.info(f"All restaurants loaded! Total: {current_count} restaurants")
                return restaurants
            
            # Count increased, continue scrolling
            previous_count = current_count
            
            # SCROLL TO BOTTOM
            await self._page.get_by_role('heading', name='Order food from the best restaurants and shops with Foodi Bangladesh', exact=False ).scroll_into_view_if_needed(timeout=10000)

            # Wait for new items to load
            try:
                await self._page.wait_for_load_state(state="networkidle", timeout=5000)
            except:
                # If networkidle times out, just wait a bit
                await self._page.wait_for_timeout(2000)

            # Add small delay for items to render
            await self._page.wait_for_timeout(1000)

            retry_count += 1

        self.logger.warning(f"Max scroll attempts ({max_retries}) reached")
        self.logger.info(f"Loaded {previous_count} restaurants")
        return restaurants

    async def scrape(self):
        """
        Main scraping logic for Foodi.

        Returns:
            List of restaurant data dictionaries
        """
        try:
            self.logger.info("Navigating to Foodi website")
            await self._page.goto("https://foodibd.com/restaurants?type=delivery")
            await self._page.wait_for_load_state(state='domcontentloaded', timeout=10000)
            time.sleep(5)

            locationDF = self.get_locations()

            scrape_meta = []

            for index, row in enumerate(locationDF.itertuples(index=False), start=1): #include locationDF.iloc[:3] for upto 3rd index execution
                lat = row.lat
                lon = row.lon
                area_name = row.area_name
                
                self.logger.debug(f"Scraping location {index}: {area_name} (lat={lat}, lon={lon})")
                self.logger.debug(f"Setting latitute: {lat}, longitude: {lon}, formatted_address: {area_name} in localStorage")
                await self._page.evaluate(
                    """([lat, lon, area_name]) => {
                        localStorage.setItem("latitude", lat);
                        localStorage.setItem("longitude", lon);
                        localStorage.setItem("formatted_address", area_name)
                    }""",
                    [str(lat), str(lon), str(area_name)]
                )
                await self._page.goto("https://foodibd.com/restaurants?type=delivery")
                self.logger.info("Page reloaded after set in localstorage")

                if index > 1:
                    self.logger.info("Waiting 15 secs between location switch")
                    time.sleep(15)

                try:
                    captcha = await self._page.locator(
                        "text=Please confirm you are a human (and not a bot)."
                    ).is_visible(timeout=25000)
                    if captcha:
                        self.logger.info("-----------Captcha found--------------")
                        await self._page.pause()
                        self.logger.info("-----------Resuming scraping after resolving captcha--------------")
                        time.sleep(30)
                except Exception as e:
                    self.logger.warning(f"-----------Captcha not found / Error Resolving Capcha/ Locator Error; trace: {e}--------------")
                    pass

                # Get all restaurant elements (don't await locator())
                restaurants_locator = await self.load_all_restaurants()
                restaurant_count = await restaurants_locator.count()
                
                self.logger.info(f"Found {restaurant_count} restaurants in {area_name}")
                await self._page.pause()

                for idx in tqdm(range(restaurant_count)):  #tqdm for visual progress bar
                    try:
                        restaurant = restaurants_locator.nth(idx)
                        
                        # Extract restaurant details (await the async methods)
                        restaurant_name = await restaurant.locator('.bds-c-vendor-tile__name').inner_text()
                        restaurant_name = restaurant_name.strip()

                        #average rating
                        rating = None
                        try:
                            rating = await restaurant.locator('.bds-c-rating__label-primary').inner_text()
                            rating = rating.strip()
                        except Exception as e:
                            self.logger.warning(f"Rating Not Available for {restaurant_name} in {area_name}; Trace: {e}")
                            rating = None
                        
                        #total review count
                        total_reviews = None
                        try:
                            total_reviews_elem = restaurant.locator('.bds-c-rating__label-secondary')
                            total_reviews_count = await total_reviews_elem.count()
                            if total_reviews_count > 0:
                                total_reviews = await total_reviews_elem.inner_text()
                        except Exception as e:
                            self.logger.warning(f"Total Review count Not Available for {restaurant_name} in {area_name}; Trace: {e}")
                            total_reviews = 0

                        # Try to get delivery fee
                        delivery_fee = None
                        try:                              
                            delivery_fee_elem = restaurant.locator("div[class='bds-c-vendor-tile__info-row bds-c-vendor-tile__info-row--delivery-fee'] > div[data-testid='bds-c-vendor-tile__info-row-text'] > div")
                            delivery_fee = await delivery_fee_elem.text_content()
                        except Exception as e:
                            self.logger.warning(f"Delivery Fee info Not Available for {restaurant_name} in {area_name}; Trace: {e}")
                            delivery_fee = "Error"

                        scrape_meta.append({
                            "area_name": area_name,
                            "restaurant_name": restaurant_name,
                            "rating": rating,
                            "total_reviews": total_reviews,
                            "delivery_fee": delivery_fee,
                        })
                    except Exception as e:
                        self.logger.warning(f"Error extracting restaurant {idx} in {area_name}: {str(e)}")
                        continue

            scrapeMetaDF = pd.DataFrame(scrape_meta)
            self.logger.info(f"Dataframe prepared for scraped data with {len(scrapeMetaDF)} restaurants")
            scrapeMetaDF.to_csv("FoodiData.csv", index=False)
            self.logger.info(f"Data saved to FoodiData.csv")

        except Exception as e:
            self.logger.error(f"Error during scraping: {str(e)}")
            await self.take_screenshot("error_foodi_v1.png")
            raise


async def main():
    """Example usage of FoodPanda v1 scraper with headers."""
    scraper = FoodiV1Scraper()
    
    try:
        await scraper.setup_scraper()
        await scraper.scrape()
        scraper.logger.info(f"✓ Scraped restaurants")
    finally:
        await scraper.teardown_browser()


if __name__ == "__main__":
    asyncio.run(main())