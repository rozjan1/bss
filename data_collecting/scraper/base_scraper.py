from abc import ABC, abstractmethod
import requests
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from time import sleep
from loguru import logger

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.models import Product

class BaseScraper(ABC):
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.session = requests.Session()
        self.all_products: List[Product] = []
        self.categories: Dict[str, str] = {}

    @abstractmethod
    def fetch_category(self, category_code: str, page: int) -> Dict[str, Any]:
        """Method to call the specific API for a retailer."""
        pass

    @abstractmethod
    def parse_response(self, response_data: Dict[str, Any], category_name: str) -> List[Product]:
        """Method to transform raw JSON into the Product Pydantic model."""
        pass

    def should_continue(self, response_data: Dict[str, Any], page: int, products: List[Product]) -> bool:
        """Hook to determine if pagination should continue."""
        return True

    def request_json(self, method: str, url: str, error_message: str, **kwargs) -> Dict[str, Any]:
        """Thin wrapper around requests that logs and returns an empty dict on failure."""
        try:
            response = self.session.request(method=method, url=url, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"{error_message}: {e}")
            return {}

    def run(self):
        """The main loop orchestrating pagination and category switching."""
        logger.info(f"Starting {self.source_name} scraper")
        
        for code, name in self.categories.items():
            logger.info(f"Scraping category: {code} ({name})")
            
            for page_index in range(0, 500):  # Large upper bound
                logger.debug(f"Fetching category {code}, page {page_index}")
                
                response_data = self.fetch_category(code, page_index)
                
                if not response_data:
                    logger.info(f"No response data for category {code} at page {page_index}")
                    break
                
                products = self.parse_response(response_data, name)
                if not products:
                    logger.info(f"No products found for category {code} at page {page_index}")
                    break

                self.all_products.extend(products)
                
                if not self.should_continue(response_data, page_index, products):
                    logger.info(f"Stopping pagination for category {code} at page {page_index}")
                    break
                
                sleep(0.1)  # Be polite to the server
        
        logger.info(f"Scraped {len(self.all_products)} products from {self.source_name}")

    def run_and_save(self, filename: str):
        """Convenience helper to run the scraper and persist results."""
        self.run()
        self.save_to_json(filename)

    def save_to_json(self, filename: str):
        """Standardized saving method."""
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving {len(self.all_products)} products to {filename}")
        with open(filename, 'w', encoding='utf-8') as f:
            json_data = [p.model_dump(mode='json') for p in self.all_products]
            json.dump(json_data, f, ensure_ascii=False, indent=2)