"""
Validators Module

Utility functions for validating and cleaning scraped data.
"""

import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid email format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str, country_code: str = "BD") -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number to validate
        country_code: Country code (default: BD for Bangladesh)

    Returns:
        True if valid phone format, False otherwise
    """
    # Remove spaces and common separators
    phone = re.sub(r'[\s\-\(\)\.]+', '', phone)

    # Bangladesh numbers
    if country_code == "BD":
        return bool(re.match(r'^(?:\+880|0)?1[1-9]\d{8}$', phone))

    # Generic pattern for other countries
    return bool(re.match(r'^\+?[1-9]\d{1,14}$', phone))


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def clean_text(text: str) -> str:
    """
    Clean and normalize text.

    - Strip whitespace
    - Remove extra spaces
    - Handle special characters

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    if not isinstance(text, str):
        return ""

    # Strip leading/trailing whitespace
    text = text.strip()

    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)

    # Remove common HTML entities
    replacements = {
        '&nbsp;': ' ',
        '&lt;': '<',
        '&gt;': '>',
        '&amp;': '&',
        '&quot;': '"',
        '&#39;': "'",
    }
    for entity, char in replacements.items():
        text = text.replace(entity, char)

    return text


def clean_price(price_str: str) -> Optional[float]:
    """
    Extract and clean price from string.

    Handles various formats like:
    - "₹1,000.50"
    - "$99.99"
    - "1000 BDT"
    - "৳500"

    Args:
        price_str: Price string to clean

    Returns:
        Cleaned price as float, None if invalid
    """
    if not isinstance(price_str, str):
        return None

    # Remove common currency symbols and text
    price_str = clean_text(price_str)
    price_str = re.sub(r'[^\d.,]', '', price_str)

    # Handle different decimal separators
    if ',' in price_str and '.' in price_str:
        # If both exist, the first is thousand separator
        price_str = price_str.replace(',', '')
    elif ',' in price_str:
        # If only comma exists, it might be decimal separator
        if price_str.count(',') == 1 and len(price_str.split(',')[1]) <= 2:
            price_str = price_str.replace(',', '.')
        else:
            price_str = price_str.replace(',', '')

    try:
        return float(price_str)
    except ValueError:
        return None


def clean_rating(rating_str: str) -> Optional[float]:
    """
    Extract and clean rating from string.

    Args:
        rating_str: Rating string to clean

    Returns:
        Cleaned rating as float, None if invalid
    """
    if not isinstance(rating_str, str):
        return None

    # Extract first number (could be like "4.5/5" or "4.5★")
    match = re.search(r'(\d+\.?\d*)', rating_str)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None

    return None


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Validate that required fields exist and are not empty.

    Args:
        data: Dictionary to validate
        required_fields: List of required field names

    Returns:
        True if all required fields exist and are non-empty
    """
    for field in required_fields:
        if field not in data or not data[field]:
            return False
    return True


def sanitize_dict(data: Dict[str, Any], allowed_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Sanitize dictionary by removing or filtering keys.

    Args:
        data: Dictionary to sanitize
        allowed_keys: List of allowed keys (removes others if provided)

    Returns:
        Sanitized dictionary
    """
    if allowed_keys is None:
        return data

    return {k: v for k, v in data.items() if k in allowed_keys}


def deduplicate_items(
    items: List[Dict[str, Any]],
    key_field: str = "id"
) -> List[Dict[str, Any]]:
    """
    Remove duplicate items from list based on a key field.

    Args:
        items: List of dictionaries
        key_field: Field to use for deduplication

    Returns:
        List without duplicates (keeps first occurrence)
    """
    seen = set()
    unique_items = []

    for item in items:
        if key_field in item:
            key_value = item[key_field]
            if key_value not in seen:
                seen.add(key_value)
                unique_items.append(item)

    return unique_items