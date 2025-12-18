from abc import ABC, abstractmethod
import requests
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.models import Product

class BaseScraper(ABC):
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.session = requests.Session()
        self.all_products: List[Product] = []

    @abstractmethod
    def fetch_category(self, category_code: str, page: int) -> Dict[str, Any]:
        """Method to call the specific API for a retailer."""
        pass

    @abstractmethod
    def parse_response(self, response_data: Dict[str, Any], category_name: str) -> List[Product]:
        """Method to transform raw JSON into the Product Pydantic model."""
        pass

    @abstractmethod
    def run(self):
        """The main loop orchestrating pagination and category switching."""
        pass

    def save_to_json(self, filename: str):
        """Standardized saving method."""
        logger.info(f"Saving {len(self.all_products)} products to {filename}")
        with open(filename, 'w', encoding='utf-8') as f:
            json_data = [p.model_dump(mode='json') for p in self.all_products]
            json.dump(json_data, f, ensure_ascii=False, indent=2)