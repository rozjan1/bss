"""
Billa-specific processor to extract structured data from raw API responses.
"""

from base_processor import BaseProcessor
from typing import List, Dict, Any
from loguru import logger
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from models.models import Product


class BillaProcessor(BaseProcessor):
    """Process raw Billa API responses into structured Product objects."""
    
    def __init__(self):
        super().__init__("billa")
    
    def parse_response(self, response_data: Dict[str, Any], category_name: str) -> List[Product]:
        """Transform Billa JSON data into Product objects."""
        products = []
        results = response_data.get("results", [])
        
        logger.debug(f"Processing {len(results)} products from category {category_name}")
        
        for product in results:
            try:
                # Basic product info
                item_name = product.get("name")
                product_slug = product.get("slug")
                
                # Category
                parent_categories = product.get("parentCategories", [[]])
                product_category = parent_categories[0][0].get("name", "Unknown Category") if parent_categories and parent_categories[0] else category_name
                
                # Image
                images = product.get("images", [])
                image_url = images[0] if images else None
                
                # Pricing
                price_data = product.get("price", {})
                regular_price_data = price_data.get("regular", {})
                loyalty_price_data = price_data.get("loyalty", {})
                
                # Original Price (convert from cents)
                original_price_cents = regular_price_data.get("value")
                if original_price_cents is None:
                    continue  # Skip products without price
                original_price = original_price_cents / 100
                
                # Sale Price and Requirements
                sale_price = original_price
                sale_ppu = None
                sale_requirement = None
                
                if loyalty_price_data:
                    sale_price_cents = loyalty_price_data.get("value")
                    if sale_price_cents is not None:
                        sale_price = sale_price_cents / 100
                        sale_requirement = "billa_card"
                
                # Price per unit
                ppu_cents = loyalty_price_data.get("perStandardizedQuantity") or regular_price_data.get("perStandardizedQuantity")
                if ppu_cents is not None:
                    sale_ppu = ppu_cents / 100
                
                # Unit code
                unit_code = price_data.get("baseUnitLong", "").lower() or None
                
                # Product URL
                product_url = f"https://shop.billa.cz/produkt/{product_slug}"
                
                # Create Product object
                product_obj = Product(
                    source="billa",
                    product_category=product_category,
                    item_name=item_name,
                    image_url=image_url,
                    original_price=original_price,
                    sale_price=sale_price,
                    sale_ppu=sale_ppu,
                    unit_code=unit_code,
                    product_url=product_url,
                    sale_requirement=sale_requirement
                )
                
                products.append(product_obj)
                
            except Exception as e:
                logger.warning(f"Failed to parse product: {e}")
                continue
        
        return products


if __name__ == "__main__":
    processor = BillaProcessor()
    processor.process_and_save('billa_processed.json')
