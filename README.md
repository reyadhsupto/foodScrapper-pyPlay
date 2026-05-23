# foodScrapper - FoodPanda Web Scraper

A robust, asynchronous web scraper built with **Playwright** and **Python** for extracting restaurant data from FoodPanda. This project demonstrates modern Python development practices with proper architecture, async patterns, anti-detection mechanisms, and comprehensive logging.

## Features

- **Async Playwright Automation**: Non-blocking browser automation with async/await patterns
- **Stealth Mode**: Built-in anti-detection using playwright-stealth to avoid blocks
- **Location-Based Scraping**: Scrape restaurants from multiple Dhaka locations via CSV
- **Infinite Scroll Handling**: Automatically loads all restaurants using infinite scroll detection
- **CAPTCHA Handling**: Pauses for manual CAPTCHA resolution with resumable scraping
- **Comprehensive Logging**: Detailed logging with timestamps and log levels
- **Data Export**: Exports scraped data to CSV format
- **Error Recovery**: Screenshot capture on errors for debugging
- **Pre-commit Hooks**: Automated code quality checks before commits
- **Docker Support**: Containerized application ready for deployment
- **Easy CLI**: Makefile commands for all common tasks

## Project Structure

```
foodScrapper-pyPlay/
├── scrapers/
│   ├── baseScraper.py                 # Abstract base scraper class (async)
│   └── foodpanda/
│       └── v1Scraper.py              # FoodPanda scraper with location support
├── utils/
│   ├── config.py                      # Configuration (ScraperConfig, FoodPandaConfig)
│   ├── logger.py                      # Logging setup with loguru
│   └── validators.py                  # Data validation helpers
├── data/
│   └── locations.csv                  # Location data (lat, lon, area_name)
├── output/
│   ├── screenshots/                   # Error screenshots
│   └── *.csv                          # Scraped data exports
├── logs/                              # Application logs
├── main.py                            # Application entry point
├── requirements.txt                   # Python dependencies
├── Makefile                           # Build automation
├── Dockerfile                         # Docker container definition
├── docker-compose.yml                 # Docker Compose configuration
├── pyproject.toml                     # Tool configurations
├── .flake8                            # Flake8 linter config
├── .prettierrc.json                   # Prettier formatter config
├── .pre-commit-config.yaml            # Pre-commit hooks
├── .editorconfig                      # EditorConfig
├── .env.example                       # Example environment variables
├── LICENSE                            # MIT License
└── README.md                          # This file
```

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Virtual environment (venv or similar)
- Chromium browser (installed automatically by Playwright)
- Git (for version control and pre-commit hooks)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/reyadhsupto/foodScrapper-pyPlay.git
   cd foodScrapper-pyPlay
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv .rvenv
   source .rvenv/bin/activate  # On Windows: .rvenv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   python3 -m playwright install chromium
   ```

4. **Copy environment variables** (optional)
   ```bash
   cp .env.example .env
   ```

5. **Install pre-commit hooks** (optional, for development)
   ```bash
   pre-commit install
   ```

### Using Makefile

The quickest way to set up:

```bash
# Install dependencies
make install

# Install dev dependencies too
make install-dev
```

## Usage

### Running the Scraper

The simplest way to run the scraper:

```bash
# Run FoodPanda v1 scraper
make scrape-foodpanda
```

This will:
1. Load 25 locations from `data/locations.csv` (first 3 by default)
2. For each location, navigate to FoodPanda with lat/lon parameters
3. Handle any CAPTCHA by pausing (await manual resolution)
4. Load all restaurants using infinite scroll
5. Extract restaurant details (name, rating, reviews, delivery fee)
6. Save results to `users.csv`

### Python Script Usage

```python
import asyncio
from scrapers.foodpanda.v1Scraper import FoodPandaV1Scraper

async def main():
    scraper = FoodPandaV1Scraper()
    
    try:
        await scraper.setup_scraper()      # Initialize browser with stealth
        await scraper.scrape()              # Run scraping logic
    finally:
        await scraper.teardown_browser()    # Clean up resources

asyncio.run(main())
```

### Customizing Locations

Edit `data/locations.csv` to add or modify locations:

```csv
lat,lon,area_name
23.8103,90.4125,Gulshan
23.7974,90.4286,Banani
23.7850,90.3563,Dhanmondi
```

### Making Screenshots on Error

When an error occurs, the scraper automatically captures a screenshot:
- Saved to: `output/screenshots/error_foodpanda_v1.png`
- Useful for debugging page state issues

## Configuration

Configuration is loaded from `utils/config.py`. Key settings:

```python
class ScraperConfig:
    # Browser settings
    headless: bool = True               # Run without GUI
    timeout: int = 30000                # Request timeout (ms)
    navigation_timeout: int = 30000     # Navigation timeout (ms)
    
    # Retry logic
    max_retries: int = 3                # Number of retry attempts
    retry_delay: float = 2.0            # Delay between retries (seconds)
    
    # Browser arguments (headless chrome)
    browser_args: List[str] = [
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--disable-setuid-sandbox",
        "--no-sandbox",
        # ... more args
    ]
    
    # Browser context
    viewport: dict = {"width": 1920, "height": 1080}
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ..."
    locale: str = "en_BD"
    timezone: str = "America/New_York"
    permissions: List[str] = ["geolocation"]
```

### Environment Variables

Create a `.env` file to override settings:

```bash
# Browser settings
HEADLESS=true
TIMEOUT=30000
NAVIGATION_TIMEOUT=30000

# Retry settings
MAX_RETRIES=3
RETRY_DELAY=2.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/scraper.log
```

## Makefile Commands

All common tasks are available via Makefile:

```bash
# Help - show all commands
make help

# Installation
make install                    # Install production dependencies
make install-dev               # Install all dependencies (prod + dev)
make setup-hooks               # Setup pre-commit hooks

# Code Quality
make lint                       # Run linters (flake8, mypy, black, isort)
make format                     # Auto-format code (black, isort)
make test                       # Run tests with coverage

# Scraping
make scrape-foodpanda          # Run FoodPanda v1 scraper
make scrape-foodpanda-v2       # Run FoodPanda v2 scraper (if available)

# Docker
make docker-build              # Build Docker image
make docker-run                # Run in Docker container
make docker-compose-up         # Start services with Docker Compose

# Cleanup
make clean                      # Remove cache, logs, and build files
make clean-output              # Remove output CSV files
make clean-screenshots         # Remove error screenshots
make clean-logs                # Clear log files
```

## Docker Deployment

### Using Docker Compose

```bash
# Start the scraper service
docker-compose up -d

# View logs
docker-compose logs -f scraper

# Stop services
docker-compose down
```

### Manual Docker Build

```bash
# Build image
make docker-build

# Run container
make docker-run

# Run with specific command
docker run --rm \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/logs:/app/logs \
  web-scraper:latest \
  python3 -m scrapers.foodpanda.v1Scraper
```

## API Reference

### BaseScraper Class

Abstract base class providing common functionality for all scrapers:

```python
class BaseScraper(ABC):
    # Browser lifecycle
    async def setup_browser()          # Initialize browser with stealth mode
    async def teardown_browser()       # Close browser and clean up
    
    # Navigation
    async def navigate(url, wait_until='networkidle')  # Navigate with retry
    
    # DOM interactions
    async def wait_for_selector(selector, timeout=None)  # Wait for element
    async def scroll_to_bottom(pause_time=1.0)          # Scroll to load dynamic content
    async def execute_script(script)                     # Execute JavaScript
    
    # Utilities
    async def take_screenshot(filename=None)  # Save screenshot for debugging
    def export_data(format='json')           # Export scraped data
    
    # Async context manager support
    async with scraper:                      # Auto cleanup on exit
        data = await scraper.scrape()
```

### FoodPandaV1Scraper Class

Specialized scraper for FoodPanda restaurants:

```python
class FoodPandaV1Scraper(BaseScraper):
    # Location management
    def get_locations() -> pd.DataFrame    # Load locations from CSV
    
    # Scraping
    async def load_all_restaurants()       # Load all via infinite scroll
    async def scrape()                     # Main scraping logic
    
    # Setup
    async def setup_scraper()              # Initialize with headers
    async def setup_browser()              # Setup browser (inherited)
```

**Example Output Format:**

```csv
area_name,restaurant_name,rating,total_reviews,delivery_fee
Gulshan,Restaurant Name,4.5,125,From Tk 50
```

## How It Works

### Scraping Flow

1. **Browser Setup**
   - Initializes Playwright async browser
   - Applies stealth mode to prevent detection
   - Creates browser context with specific locale/timezone

2. **Location Iteration**
   - Reads locations from `data/locations.csv`
   - For each location, constructs URL with lat/lon parameters
   - Navigates to `https://www.foodpanda.com.bd/?lat={lat}&lng={lon}`

3. **CAPTCHA Handling**
   - Detects CAPTCHA challenge text
   - Pauses execution with `await page.pause()`
   - Waits for manual resolution (60 seconds)
   - Resumes automatically after timeout

4. **Infinite Scroll Loading**
   - Gets initial restaurant count
   - Scrolls to bottom of page
   - Waits for page to stabilize (`networkidle`)
   - Repeats until restaurant count stops increasing
   - Logs progress at each step

5. **Data Extraction**
   - For each restaurant element, extracts:
     - Restaurant name (CSS: `.bds-c-vendor-tile__name`)
     - Rating (CSS: `.bds-c-rating__label-primary`)
     - Review count (CSS: `.bds-c-rating__label-secondary`)
     - Delivery fee (CSS: `div:has-text('From Tk')`)
   - Handles missing values gracefully

6. **Data Export**
   - Collects all restaurant data
   - Creates pandas DataFrame
   - Exports to `users.csv`

### Anti-Detection Mechanisms

- **Stealth Mode**: Hides automation indicators
- **User Agent**: Mimics real Chrome browser
- **Viewport**: Set to 1920x1080 (realistic size)
- **Locale**: Set to en_BD (Bangladesh)
- **Timezone**: Set to America/New_York
- **Delays**: 5 second wait between page loads, 15 second delay between locations
- **Request Timeouts**: Proper timeout handling for flaky networks

## Performance Tuning

### Speed Optimization
- Set `headless=True` (faster rendering)
- Reduce `timeout` values if connection is fast
- Scrape during off-peak hours (less server load)

### Stability Improvements
- Increase `retry_delay` if experiencing timeouts
- Increase `navigation_timeout` for slow connections
- Add longer delays between locations if getting rate-limited
- Use residential proxies if IP-based blocking occurs

### Resource Management
- Close browser after each location (reduce memory)
- Scrape locations in batches
- Clear logs periodically with `make clean-logs`

## Troubleshooting

### Browser Issues

**"Browser has been closed" error**
- Solution: Removed `--single-process` from browser args (was causing instability)
- Ensure sufficient system memory (4GB+ recommended)

**Stealth mode not working**
- Verify `playwright-stealth` is installed: `pip list | grep playwright-stealth`
- Check browser is headless (`headless=True`)
- Try disabling other browser args that might conflict

### Scraping Issues

**No restaurants found**
- Check internet connection
- Verify lat/lon coordinates are correct
- Try opening URL in regular browser manually
- Check if FoodPanda is available in that region

**CAPTCHA appears every time**
- FoodPanda may be blocking your IP
- Wait 24 hours before retrying
- Try using a different network/proxy
- Increase delay between location changes

**Slow scraping**
- Normal: ~1-2 minutes per 700 restaurants
- Consider running multiple locations concurrently
- Check network speed with `speedtest-cli`
- Reduce `wait_for_load_state` timeout if connection is fast

**Missing restaurant data**
- Some fields may not exist for all restaurants (ratings, delivery fee)
- Code handles this by returning `None` for missing fields
- Check output CSV for which fields are populated

### Logging

Enable debug logging for troubleshooting:

```bash
# Set in .env or command line
export LOG_LEVEL=DEBUG
make scrape-foodpanda
```

Logs are saved to `logs/scraper.log` with timestamps and levels.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and commit: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

Please ensure:
- Code follows project style (run `make format`)
- All tests pass (run `make test`)
- Linters pass (run `make lint`)
- Changes are documented

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational purposes. Always respect websites' `robots.txt`, `Terms of Service`, and rate limits. The authors are not responsible for misuse of this scraper. Use responsibly and ethically.

## Support & Feedback

- 🐛 Found a bug? Open an [issue](https://github.com/reyadhsupto/foodScrapper-pyPlay/issues)
- 💡 Have a feature idea? Create a discussion
- 📧 Questions? Reach out via email

## Acknowledgments

- [Playwright](https://playwright.dev/) - Browser automation library
- [playwright-stealth](https://github.com/evasion-tech/playwright-stealth) - Anti-detection plugin
- [loguru](https://github.com/Delgan/loguru) - Advanced logging
- [pandas](https://pandas.pydata.org/) - Data manipulation
- [tqdm](https://tqdm.github.io/) - Progress bars

## Changelog

### Version 0.1.0 (Current)
- Initial project release
- FoodPanda v1 scraper with location support
- Infinite scroll handling
- CAPTCHA detection and pause
- CSV data export
- Stealth mode integration
- Comprehensive logging with loguru
- Docker support
- Pre-commit hooks
- Makefile automation
