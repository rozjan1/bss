import sys
from typing import Dict, Any
from pathlib import Path
from loguru import logger

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from utils.openfoodfacts_utils import OpenFoodFactsFetcher
from base_enricher import BaseProductEnricher


class OpenFoodFactsEnricher(BaseProductEnricher):
    """
    Enricher that uses OpenFoodFacts API to fetch product information by barcode.
    
    Input file products should have a 'barcode' field with the product's EAN/UPC code.
    """
    
    def __init__(self, input_file: str = None, output_file: str = None, num_workers: int = 4):
        # Default paths
        if input_file is None:
            input_file = str(Path(__file__).parent.parent / 'data' / 'products_with_barcodes.json')
        if output_file is None:
            output_file = str(Path(__file__).parent.parent / 'data' / 'openfoodfacts_enriched.json')
        
        super().__init__(
            input_file=input_file,
            output_file=output_file,
            num_workers=num_workers  # Use fewer workers to be respectful to the API
        )
        self.fetcher = OpenFoodFactsFetcher()
    
    def get_product_info(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch product information from OpenFoodFacts using barcode.
        
        Args:
            product: Product dict that must contain a 'barcode' field
            
        Returns:
            Dict with 'nutrition', 'allergies', 'ingredients'
        """
        barcode = product.get('barcode') or product.get('ean') or product.get('gtin')
        
        if not barcode:
            logger.warning(f"Product {product.get('item_name', 'Unknown')} missing barcode")
            return {'nutrition': {}, 'allergies': {}, 'ingredients': None}
        
        try:
            info = self.fetcher.fetch(barcode)
            return info
        except Exception as e:
            # Log warning but don't raise - let the base class handle it
            logger.debug(f"Failed to fetch barcode {barcode}: {e}")
            raise  # Re-raise to trigger retry logic in base class


if __name__ == '__main__':
    import sys
    
    # Allow passing custom input/output files as command line arguments
    if len(sys.argv) >= 3:
        enricher = OpenFoodFactsEnricher(
            input_file=sys.argv[1],
            output_file=sys.argv[2],
            num_workers=int(sys.argv[3]) if len(sys.argv) > 3 else 4
        )
    else:
        enricher = OpenFoodFactsEnricher()
    
    logger.info("Starting OpenFoodFacts enrichment...")
    logger.info(f"Input: {enricher.input_file}")
    logger.info(f"Output: {enricher.output_file}")
    enricher.enrich_products()
    logger.info("Enrichment complete!")
