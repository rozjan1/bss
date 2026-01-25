"""
Base processor for extracting structured data from raw scraped responses.

This stage separates data extraction from scraping, allowing us to:
1. Reprocess raw data without hitting APIs again
2. Modify extraction logic independently
3. Test extraction logic without scraping
"""

from abc import ABC, abstractmethod
import json
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
import sys

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.models import Product


class BaseProcessor(ABC):
    """Base class for processing raw scraped data into structured products."""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.all_products: List[Product] = []
        
        # Setup logging
        self.logs_dir = Path(__file__).parent / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        logger.add(self.logs_dir / "processor.log", level="INFO", rotation="1 day")
        
        # Paths - raw data is now in data_collecting/data/raw/
        self.raw_data_dir = Path(__file__).parent.parent / "data" / "raw" / source_name
        self.output_dir = Path(__file__).parent.parent / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def parse_response(self, response_data: Dict[str, Any], category_name: str) -> List[Product]:
        """
        Transform raw JSON response into Product objects.
        This method should be implemented by each retailer-specific processor.
        """
        pass
    
    def process_all_raw_files(self):
        """Process all raw JSON files in the raw data directory."""
        logger.info(f"Processing raw data from {self.raw_data_dir}")
        
        if not self.raw_data_dir.exists():
            logger.error(f"Raw data directory not found: {self.raw_data_dir}")
            return
        
        raw_files = sorted(self.raw_data_dir.glob("*.json"))
        
        if not raw_files:
            logger.warning(f"No raw files found in {self.raw_data_dir}")
            return
        
        logger.info(f"Found {len(raw_files)} raw files to process")
        
        for raw_file in raw_files:
            try:
                logger.debug(f"Processing {raw_file.name}")
                
                with open(raw_file, 'r', encoding='utf-8') as f:
                    response_data = json.load(f)
                
                # Extract category name from filename (e.g., "category_page_0.json" -> "category")
                category_name = raw_file.stem.rsplit('_page_', 1)[0]
                
                products = self.parse_response(response_data, category_name)
                
                if products:
                    self.all_products.extend(products)
                    logger.debug(f"Extracted {len(products)} products from {raw_file.name}")
                else:
                    logger.debug(f"No products extracted from {raw_file.name}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from {raw_file.name}: {e}")
            except Exception as e:
                logger.error(f"Error processing {raw_file.name}: {e}")
        
        logger.info(f"Total products extracted: {len(self.all_products)}")
    
    def save_to_json(self, filename: str):
        """Save processed products to JSON file."""
        output_path = self.output_dir / filename
        
        logger.info(f"Saving {len(self.all_products)} products to {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json_data = [p.model_dump(mode='json') for p in self.all_products]
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully saved to {output_path}")
    
    def process_and_save(self, filename: str):
        """Convenience method to process all files and save."""
        self.process_all_raw_files()
        self.save_to_json(filename)
