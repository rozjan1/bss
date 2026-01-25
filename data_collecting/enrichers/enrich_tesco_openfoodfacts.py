"""
Tesco Product Enricher using OpenFoodFacts API.

This enricher attempts to fetch product information from OpenFoodFacts
using barcodes. Since Tesco products may not all have barcodes in the 
raw data, this enricher can be used as a fallback or alternative enrichment
strategy when barcode data becomes available.

For products without barcodes, the enricher returns empty/null values.
"""

import sys
from typing import Dict, Any
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.openfoodfacts_utils import OpenFoodFactsFetcher
from base_enricher import BaseProductEnricher


class TescoOpenFoodFactsEnricher(BaseProductEnricher):
    """
    Tesco enricher using OpenFoodFacts API via barcode lookup.
    
    This is a simpler alternative to the complex HTML scraping approach.
    Requires products to have a 'barcode' field.
    """
    
    def __init__(self):
        super().__init__(
            input_file=str(Path(__file__).parent.parent / 'data' / 'tesco_processed.json'),
            output_file=str(Path(__file__).parent.parent / 'data' / 'tesco_enriched.json'),
            num_workers=4  # Use fewer workers to be respectful to the API
        )
        self.fetcher = OpenFoodFactsFetcher()
    
    def get_product_info(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch product information from OpenFoodFacts using barcode.
        
        Args:
            product: Product dict that should contain a 'barcode' field
            
        Returns:
            Dict with 'nutrition', 'allergies', 'ingredients'
        """
        # Try multiple possible barcode field names
        barcode = (
            product.get('barcode') or 
            product.get('ean') or 
            product.get('gtin') or
            product.get('ean13')
        ) # Tesco only uses gtin, but this makes it more robust
        
        if not barcode:
            logger.warning(
                f"Product {product.get('item_name', 'Unknown')} missing barcode, "
                "cannot enrich from OpenFoodFacts"
            )
            return {
                'nutrition': {}, 
                'allergies': {
                    'Obsahuje': []
                }, 
                'ingredients': None
            }
        
        try:
            info = self.fetcher.fetch(barcode)
            
            # Ensure the allergies format matches what Tesco expects
            # (Tesco original only had 'Obsahuje' array)
            if 'allergies' in info and isinstance(info['allergies'], dict):
                # Combine "Obsahuje" and "Může obsahovat" into single list
                contains = info['allergies'].get('Obsahuje', [])
                may_contain = info['allergies'].get('Může obsahovat', [])
                all_allergens = contains + may_contain
                
                info['allergies'] = {
                    'Obsahuje': all_allergens
                }
            
            return info
            
        except Exception as e:
            logger.debug(f"Failed to fetch barcode {barcode}: {e}")
            raise  # Re-raise to trigger retry logic in base class


if __name__ == '__main__':
    logger.info("Starting Tesco enrichment using OpenFoodFacts...")
    enricher = TescoOpenFoodFactsEnricher()
    enricher.enrich_products()
    logger.info("Enrichment complete!")
