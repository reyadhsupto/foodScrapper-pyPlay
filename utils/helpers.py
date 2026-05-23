"""
Utilities Module
Common utility functions for the scraper application.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def setup_logging(log_level: str = "INFO", log_file: str = "scraper.log") -> None:
    """
    Setup logging configuration.

    Args:
        log_level (str): Logging level. Defaults to "INFO".
        log_file (str): Log file path. Defaults to "scraper.log".
    """
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def save_json(data: Dict[str, Any], filepath: str) -> None:
    """
    Save data to a JSON file.

    Args:
        data (Dict[str, Any]): Data to save.
        filepath (str): Path to save the JSON file.
    """
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logging.info(f"Data saved to {filepath}")

    except Exception as e:
        logging.error(f"Failed to save JSON: {str(e)}")
        raise


def load_json(filepath: str) -> Dict[str, Any]:
    """
    Load data from a JSON file.

    Args:
        filepath (str): Path to the JSON file.

    Returns:
        Dict[str, Any]: Loaded data.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    except Exception as e:
        logging.error(f"Failed to load JSON: {str(e)}")
        raise


def get_timestamp() -> str:
    """
    Get current timestamp in ISO format.

    Returns:
        str: Current timestamp.
    """
    return datetime.now().isoformat()


def format_filename(prefix: str, extension: str = "json") -> str:
    """
    Generate a timestamped filename.

    Args:
        prefix (str): Prefix for the filename.
        extension (str): File extension. Defaults to "json".

    Returns:
        str: Formatted filename.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"
