import re
from typing import Optional

def parse_price_string(price_str: str) -> Optional[float]:
    """
    Parses a price string like "12,90", "12.90", "1 290,00" into a float.
    Removes currency symbols (Kč, €) and whitespace.
    """
    if not price_str:
        return None
    
    # Remove non-breaking spaces and normal spaces
    cleaned = price_str.replace("\xa0", "").replace(" ", "")
    # Remove currency symbols
    cleaned = cleaned.replace("Kč", "").replace("€", "")
    
    # Handle comma as decimal separator
    # If there are multiple dots, it might be thousands separator (e.g. 1.290,00)
    # But usually in CZ/EU it's space or dot for thousands and comma for decimal.
    # Or space for thousands and comma for decimal.
    
    # Simple strategy: replace comma with dot
    cleaned = cleaned.replace(",", ".")
    
    # Remove any remaining non-numeric chars except dot
    # (This might be dangerous if there are other things, but for price strings it's usually fine)
    
    try:
        return float(cleaned)
    except ValueError:
        return None

def extract_price_with_currency(text: str, currency: str = "Kč") -> Optional[float]:
    """
    Extracts a price followed by a currency symbol from text.
    Example: "Cena: 12,90 Kč" -> 12.90
    """
    if not text:
        return None
        
    # Regex to find number before currency
    # Matches: 12,90 or 12.90 or 12
    # Followed by optional space and currency
    pattern = r'(\d+(?:[.,]\d{1,2})?)\s*' + re.escape(currency)
    match = re.search(pattern, text)
    
    if match:
        price_part = match.group(1)
        return parse_price_string(price_part)
    return None
