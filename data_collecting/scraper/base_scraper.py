from abc import ABC, abstractmethod
import requests
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from time import sleep
from loguru import logger

# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.models import Product

class BaseScraper(ABC):
    def __init__(self, source_name: str, enable_checkpoints: bool = True):
        self.source_name = source_name
        self.session = requests.Session()
        self.all_products: List[Product] = []
        self.categories: Dict[str, str] = {}
        
        # Checkpoint configuration
        self.enable_checkpoints = enable_checkpoints
        self.checkpoint_dir = Path(__file__).parent / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / f"{source_name}_checkpoint.json"
        self.partial_data_file = self.checkpoint_dir / f"{source_name}_partial_data.json"

        # Logging configuration
        self.logs_dir = Path(__file__).parent / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        # saving logs to a file
        logger.add(self.logs_dir / "scraper.log", level="ERROR", rotation="1 day")
        logger.add(self.logs_dir / "errors.log", level="DEBUG", rotation="1 day")

    @abstractmethod
    def fetch_category(self, category_code: str, page: int) -> Dict[str, Any]:
        """Method to call the specific API for a retailer."""
        pass

    def save_checkpoint(self, category_code: str, page: int):
        """Save current progress checkpoint."""
        if not self.enable_checkpoints:
            return
        
        checkpoint_data = {
            "source": self.source_name,
            "last_category": category_code,
            "last_page": page,
            "total_products": len(self.all_products),
            "timestamp": str(Path(__file__).stat().st_mtime if self.checkpoint_file.exists() else "")
        }
        
        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2)
            logger.debug(f"Checkpoint saved: {category_code} page {page}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def load_checkpoint(self) -> Tuple[str, int]:
        """Load checkpoint and return (category_code, page) to resume from."""
        if not self.enable_checkpoints or not self.checkpoint_file.exists():
            return None, None
        
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            category = checkpoint_data.get("last_category")
            page = checkpoint_data.get("last_page", 0) + 1  # Start from next page
            logger.info(f"Checkpoint loaded: resuming from {category} page {page}")
            return category, page
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None, None

    def save_partial_data(self):
        """Save partial/intermediate results."""
        if not self.enable_checkpoints:
            return
        
        try:
            with open(self.partial_data_file, 'w', encoding='utf-8') as f:
                json_data = [p.model_dump(mode='json') for p in self.all_products]
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Partial data saved: {len(self.all_products)} products")
        except Exception as e:
            logger.error(f"Failed to save partial data: {e}")

    def load_partial_data(self) -> List[Product]:
        """Load partial data from previous run."""
        if not self.enable_checkpoints or not self.partial_data_file.exists():
            return []
        
        try:
            with open(self.partial_data_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            products = [Product(**item) for item in json_data]
            logger.info(f"Partial data loaded: {len(products)} products")
            return products
        except Exception as e:
            logger.error(f"Failed to load partial data: {e}")
            return []

    def clear_checkpoint(self):
        """Clear checkpoint files after successful completion."""
        if not self.enable_checkpoints:
            return
        
        try:
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
            if self.partial_data_file.exists():
                self.partial_data_file.unlink()
            logger.info("Checkpoint and partial data cleared")
        except Exception as e:
            logger.error(f"Failed to clear checkpoint: {e}")

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

    def request_json(self, method: str, url: str, error_message: str, max_retries: int = 5, **kwargs) -> Dict[str, Any]:
        """Thin wrapper around requests that logs and returns an empty dict on failure."""
        for attempt in range(max_retries):
            try:
                response = self.session.request(method=method, url=url, **kwargs)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 503:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(f"503 Service Unavailable. Retrying in {wait_time}s...")
                        sleep(wait_time)
                        continue
                logger.error(f"{error_message}: {e}")
                return {}
            except Exception as e:
                logger.error(f"{error_message}: {e}")
                return {}
        return {}

    def run(self, resume: bool = True):
        """The main loop orchestrating pagination and category switching with checkpoint support."""
        logger.info(f"Starting {self.source_name} scraper")
        
        # Load partial data if resuming
        if resume:
            self.all_products = self.load_partial_data()
        
        # Get resume point from checkpoint
        resume_category, resume_page = None, None
        if resume:
            resume_category, resume_page = self.load_checkpoint()
        
        # Build list of categories to process
        categories_list = list(self.categories.items())
        start_index = 0
        
        # Find starting position if resuming
        if resume_category:
            try:
                start_index = next(i for i, (code, _) in enumerate(categories_list) if code == resume_category)
            except StopIteration:
                logger.warning(f"Resume category {resume_category} not found, starting from beginning")
                start_index = 0
                resume_page = None
        
        # Process categories
        for idx, (code, name) in enumerate(categories_list[start_index:], start=start_index):
            start_page = resume_page if (resume_category and code == resume_category) else 0
            logger.info(f"Scraping category: {code} ({name})")
            
            for page_index in range(start_page, 500):  # Large upper bound
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
                
                # Save checkpoint and partial data periodically
                self.save_checkpoint(code, page_index)
                self.save_partial_data()
                
                if not self.should_continue(response_data, page_index, products):
                    logger.info(f"Stopping pagination for category {code} at page {page_index}")
                    break
                
                sleep(0.1)  # Be polite to the server
        
        logger.info(f"Scraped {len(self.all_products)} products from {self.source_name}")
        # Clear checkpoint after successful completion
        self.clear_checkpoint()

    def run_and_save(self, filename: str, resume: bool = True):
        """Convenience helper to run the scraper and persist results."""
        self.run(resume=resume)
        self.save_to_json(filename)

    def save_to_json(self, filename: str):
        """Standardized saving method."""
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving {len(self.all_products)} products to {filename}")
        with open(filename, 'w', encoding='utf-8') as f:
            json_data = [p.model_dump(mode='json') for p in self.all_products]
            json.dump(json_data, f, ensure_ascii=False, indent=2)