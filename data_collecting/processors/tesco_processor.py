"""
Tesco-specific processor to extract structured data from raw API responses.
"""

from base_processor import BaseProcessor
from typing import List, Dict, Any
from loguru import logger
import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent.parent))
from models.models import Product
from utils.price_utils import extract_price_with_currency


class TescoProcessor(BaseProcessor):
    """Process raw Tesco API responses into structured Product objects."""
    
    def __init__(self):
        super().__init__("tesco")
    
    def parse_response(self, response_data: Dict[str, Any], category_name: str) -> List[Product]:
        """Transform Tesco JSON data into Product objects."""
        products: List[Product] = []
        
        try:
            results_list = response_data[0]["data"]["category"]["results"]
        except (IndexError, KeyError) as e:
            logger.warning(f"Could not find 'results' list for category {category_name}: {e}")
            return products
        
        logger.debug(f"Processing {len(results_list)} products from category {category_name}")
        
        for item in results_list:
            try:
                node = item["node"]
                
                # Basic info
                title = node["title"]
                image_url = node["defaultImageUrl"]
                
                # Pricing
                seller_info = node["sellers"]["results"][0]
                regular_price_raw = seller_info["price"].get("price")
                price_per_unit_default = seller_info["price"].get("unitPrice")
                
                # Skip items without a numeric price
                if regular_price_raw is None:
                    continue
                
                try:
                    regular_price = float(regular_price_raw)
                except (TypeError, ValueError):
                    continue
                
                sale_price = regular_price
                sale_ppu = float(price_per_unit_default) if price_per_unit_default is not None else None
                sale_requirement = None
                
                # Check for promotions
                promotions = seller_info["promotions"]
                
                if promotions:
                    promotion = promotions[0]
                    description = promotion["description"]
                    promo_attributes = promotion.get("attributes", [])
                    
                    if promo_attributes:
                        if promo_attributes[0] == 'CLUBCARD_PRICING':
                            sale_requirement = 'tesco_clubcard'
                    
                    if "s Clubcard" in description:
                        if not re.search(r'\d{1,3}%.*předtím', description):
                            extracted_price = extract_price_with_currency(description)
                            if extracted_price is not None:
                                sale_price = extracted_price
                        
                        # Extract unit price from promotion
                        unit_selling_info = promotion.get('unitSellingInfo', '')
                        if unit_selling_info:
                            try:
                                sale_ppu = float(unit_selling_info.split(" ")[0].replace(",", "."))
                            except (ValueError, IndexError):
                                pass
                
                unit_code = seller_info["price"]["unitOfMeasure"]
                product_url = f"https://nakup.itesco.cz/groceries/cs-CZ/products/{node['id']}"
                
                # Create Product object
                product_obj = Product(
                    source="tesco",
                    product_category=category_name,
                    item_name=title,
                    image_url=image_url,
                    original_price=regular_price,
                    original_ppu=float(price_per_unit_default) if price_per_unit_default is not None else None,
                    sale_price=sale_price,
                    sale_ppu=sale_ppu,
                    unit_code=unit_code,
                    product_url=product_url,
                    sale_requirement=sale_requirement
                )
                
                products.append(product_obj)
                
            except (KeyError, IndexError) as e:
                logger.warning(f"Error processing item: {e}")
                continue
        
        return products


if __name__ == "__main__":
    processor = TescoProcessor()
    processor.process_and_save('tesco_processed.json')
