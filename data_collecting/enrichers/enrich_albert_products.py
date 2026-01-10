from typing import Dict, Any
from pathlib import Path
from loguru import logger
from base_enricher import BaseProductEnricher
from albert_get_product_info import AlbertProductInfoFetcher

class AlbertEnricher(BaseProductEnricher):
    def __init__(self):
        super().__init__(
            input_file=str(Path(__file__).parent.parent / 'data' / 'albert_raw.json'),
            output_file=str(Path(__file__).parent.parent / 'data' / 'albert_enriched.json'),
            num_workers=8
        )
        self.fetcher = AlbertProductInfoFetcher()

    def get_product_info(self, product: Dict[str, Any]) -> Dict[str, Any]:
        url = product.get('product_url') or product.get('url')
        if not url:
            logger.warning(f"Product {product.get('name', 'Unknown')} missing URL")
            return {'nutrition': {}, 'allergies': {}, 'ingredients': None}
        
        info = self.fetcher.fetch(url)
        return {
            'nutrition': info.get('nutrients', {}),
            'allergies': info.get('allergies', {}),
            'ingredients': info.get('ingredients')
        }



if __name__ == '__main__':
    enricher = AlbertEnricher()
    enricher.enrich_products()
