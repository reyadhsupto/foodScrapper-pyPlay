# scrapers/foodpanda/v1Scrapper.py

"""
FoodPanda v1 Scraper with API Headers

Version 1: Basic implementation for scraping restaurants from FoodPanda.

This version includes:
- Restaurant listing extraction
- Header interception and management

Key Headers:
- x-fp-api-key: "volo" (FoodPanda API key)
- apollographql-client-name: "web" (Client identifier)
- locale: "en_BD" (Language/region)
- customer-latitude/longitude: (Location-based results)
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
from utils.config import FoodPandaConfig
from utils.logger import get_logger
from utils.validators import clean_price, clean_rating, clean_text


class FoodPandaV1Scraper(BaseScraper):
    """
    FoodPanda v1 Scraper - With proper API headers.

    This scraper handles:
    - FoodPanda-specific request headers
    - GraphQL API requests
    - Location-based restaurant filtering
    - Session and tracking ID management

    Example usage:
    ```python
    async def main():
        scraper = FoodPandaV1Scraper()
        scraper.set_location(latitude=23.8103, longitude=90.4125)
        data = await scraper.run()
        print(f"Scraped {len(data)} restaurants")

    asyncio.run(main())
    ```
    """

    def __init__(self):
        """Initialize FoodPanda v1 scraper."""
        super().__init__(
            website_name="foodpanda",
            version="v1"
        )
        
        # Session management
        self.session_id = None
        self.perseus_id = None
        self.dps_session_id = None
        
        # Headers cache
        self._context_headers = None
        self._logger = get_logger(f"{self.website_name}_{self.version}_headers")

    def get_locations(self) -> pd.DataFrame:
        """
        Read locations from CSV file and return as pandas DataFrame.

        Returns a DataFrame containing (latitude, longitude, area_name)
        from the locations.csv file with columns: lat, lon, area_name.

        Returns:
            pd.DataFrame: DataFrame with columns ['lat', 'lon', 'area_name']
                         and data types:
                         - lat: float64
                         - lon: float64
                         - area_name: object (string)

        Raises:
            FileNotFoundError: If locations.csv is not found
            ValueError: If CSV is malformed

        Example:
            >>> scraper = FoodPandaV1Scraper()
            >>> locations_df = scraper.get_locations()
            >>> print(locations_df.head())
               lat      lon     area_name
            0  23.8103  90.4125     Gulshan
            1  23.7974  90.4286      Banani
            ...
            >>> # Iterate through locations
            >>> for idx, row in locations_df.iterrows():
            ...     scraper.set_location(row['lat'], row['lon'])
            ...     restaurants = await scraper.run()
        """
        csv_path = Path(__file__).parent.parent.parent / "data" / "locations.csv"

        if not csv_path.exists():
            self.logger.error(f"Locations CSV not found at: {csv_path}")
            raise FileNotFoundError(f"Locations CSV not found at: {csv_path}")

        try:
            # Read CSV directly into DataFrame
            df = pd.read_csv(
                csv_path,
                dtype={
                    'lat': float,
                    'lon': float,
                    'area_name': str
                }
            )

            # Remove rows with missing values
            initial_count = len(df)
            df = df.dropna()
            dropped_count = initial_count - len(df)

            if dropped_count > 0:
                self.logger.warning(f"Dropped {dropped_count} rows with missing values")

            # Strip whitespace from area_name
            df['area_name'] = df['area_name'].str.strip()

            # Remove empty area names
            df = df[df['area_name'].str.len() > 0]

            # Reset index
            df = df.reset_index(drop=True)

            # Log summary
            self.logger.info(f"Loaded {len(df)} locations from CSV with Columns: {list(df.columns)}, Shape: {df.shape}")

            return df

        except pd.errors.ParserError as e:
            self.logger.error(f"CSV parsing error: {str(e)}")
            raise ValueError(f"CSV parsing error: {str(e)}") from e
        except ValueError as e:
            self.logger.error(f"Data validation error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error reading locations CSV: {str(e)}")
            raise

    async def setup_scraper(self) -> None:
        """
        Setup browser with FoodPanda-specific headers.

        Configures:
        - Context-level headers (apply to all requests)
        - Request interception for dynamic headers
        - Session tracking IDs
        """

        # pass website wise context level extra http headers
        await self.setup_browser()

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
            restaurants = self._page.locator("//ul[@data-testid='vendor-list-revamped-section']/li")
            current_count = await restaurants.count()
            
            self.logger.info(f"Scroll attempt {retry_count + 1}: Found {current_count} restaurants")
            
            # Check if count increased
            if current_count == previous_count:
                self.logger.info(f"All restaurants loaded! Total: {current_count}")
                return restaurants
            
            # Count increased, continue scrolling
            previous_count = current_count
            
            # SCROLL TO BOTTOM
            await self._page.locator("strong:has-text('Fast food delivery in')").scroll_into_view_if_needed(timeout=30000)

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
        Main scraping logic for FoodPanda.

        Returns:
            List of restaurant data dictionaries
        """
        try:

            locationDF = self.get_locations()

            scrape_meta = []

            for index, row in enumerate(locationDF.itertuples(index=False), start=1): #include locationDF.iloc[:3] for upto 3rd index execution
                lat = row.lat
                lon = row.lon
                area_name = row.area_name
                
                self.logger.info(f"Scraping location {index}: {area_name} (lat={lat}, lon={lon})")

                if index > 1:
                    # await self._page.wait_for_timeout(15000)
                    self.logger.info("Waiting 15 secs between location switch")
                    time.sleep(15)

                await self._page.goto(f"https://www.foodpanda.com.bd/?lat={lat}&lng={lon}")
                await self._page.wait_for_load_state(state='domcontentloaded', timeout=10000)
                # await self._page.wait_for_timeout(timeout=3000)
                time.sleep(5)

                try:
                    captcha = await self._page.locator(
                        "text=Please confirm you are a human (and not a bot)."
                    ).is_visible(timeout=25000)
                    if captcha:
                        self.logger.info("-----------Captcha found--------------")
                        await self._page.pause()
                        self.logger.info("-----------Resuming scraping after resolving captcha--------------")
                        # await self._page.wait_for_timeout(60000)  # Wait for solve
                        time.sleep(30)
                except Exception as e:
                    self.logger.warning(f"-----------Captcha not found / Error Resolving Capcha/ Locator Error; trace: {e}--------------")
                    pass

                # Get all restaurant elements (don't await locator())
                restaurants_locator = await self.load_all_restaurants()
                restaurant_count = await restaurants_locator.count()
                
                self.logger.info(f"Found {restaurant_count} restaurants in {area_name}")

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
            scrapeMetaDF.to_csv("users.csv", index=False)
            self.logger.info(f"Data saved to users.csv")

        except Exception as e:
            self.logger.error(f"Error during scraping: {str(e)}")
            await self.take_screenshot("error_foodpanda_v1.png")
            raise


async def main():
    """Example usage of FoodPanda v1 scraper with headers."""
    scraper = FoodPandaV1Scraper()
    
    try:
        await scraper.setup_scraper()
        await scraper.scrape()
        scraper.logger.info(f"✓ Scraped restaurants")
    finally:
        await scraper.teardown_browser()


if __name__ == "__main__":
    asyncio.run(main())