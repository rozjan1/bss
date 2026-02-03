import json
import threading
import time
import shutil
from queue import Queue, Empty
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from pathlib import Path
from loguru import logger

class BaseProductEnricher(ABC):
    def __init__(self, input_file: str, output_file: str, num_workers: int = 8):
        self.input_file = input_file
        self.output_file = output_file
        self.num_workers = num_workers
        self.results_lock = threading.Lock()
        self.enriched_products: Dict[str, Dict[str, Any]] = {}
        self.input_products_data: List[Dict[str, Any]] = []

        # Configure logging
        self.logs_dir = Path(__file__).parent / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        # Add a file sink for logs
        logger.add(self.logs_dir / "enricher.log", rotation="1 day", level="INFO")

    def _get_product_id(self, p: Dict[str, Any]) -> str:
        return p.get('product_url') or p.get('url') or p.get('id')

    def _load_checkpoint(self) -> Dict[str, Dict[str, Any]]:
        output_path = Path(self.output_file)
        if not output_path.exists():
            return {}
        
        try:
            logger.info(f"Loading checkpoint from {self.output_file}...")
            with open(self.output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                logger.warning(f"Checkpoint file content is not a list. Starting fresh.")
                return {}

            loaded_map = {}
            for item in data:
                pid = self._get_product_id(item)
                if pid:
                    # Basic validation: ensure it has at least 'nutrition' or key fields
                    # to distinguish from a raw item if we ever save mixed lists.
                    # For now, we assume anything in output file is 'processed'.
                    loaded_map[pid] = item
                    
            logger.info(f"Loaded {len(loaded_map)} products from checkpoint.")
            return loaded_map
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}. Starting fresh.")
            return {}

    def _save_checkpoint(self) -> bool:
        # Save currently enriched products to a temp file then move it
        # Returns True if saved, False if skipped (no changes)
        try:
            with self.results_lock:
                current_count = len(self.enriched_products)
                # Only save if we have new data since last explicit save or generic check
                # For simplicity in this method, we can just save. 
                # But to avoid log spam, we checks outside or silence log.
                data_to_save = list(self.enriched_products.values())
            
            # Optimization: If we had a mechanism to track changes, we could skip IO.
            # But the user complains about LOG spam. 
            
            temp_file = Path(self.output_file).with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
            
            shutil.move(str(temp_file), self.output_file)
            return True
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False

    def enrich_products(self):
        logger.info(f"Loading products from {self.input_file}...")
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                self.input_products_data = json.load(f)
        except FileNotFoundError:
             logger.error(f"Input file {self.input_file} not found.")
             return

        logger.info(f"Found {len(self.input_products_data)} products total.")
        
        # Load existing progress
        self.enriched_products = self._load_checkpoint()
        last_save_count = len(self.enriched_products)
        
        # Determine missing products
        products_to_process = []
        for p in self.input_products_data:
            pid = self._get_product_id(p)
            if pid and pid not in self.enriched_products:
                products_to_process.append(p)

        if not products_to_process:
            logger.info("All products already enriched! Performing final sort and save.")
            self._save_final_output()
            return

        logger.info(f"Starting {self.num_workers} workers to process {len(products_to_process)} remaining products...")
        
        task_queue: Queue = Queue()
        for p in products_to_process:
            task_queue.put(p)

        workers = [
            EnricherWorker(task_queue, self, i) 
            for i in range(self.num_workers)
        ]
        for w in workers:
            w.start()

        # Monitoring loop
        try:
            while any(w.is_alive() for w in workers):
                time.sleep(5) # Check every 5 seconds
                
                # Only save and log if count changed
                current_len = len(self.enriched_products)
                if current_len > last_save_count:
                    if self._save_checkpoint():
                        logger.debug(f"Checkpoint saved: {current_len} items.")
                        last_save_count = current_len
                
        except KeyboardInterrupt:
            logger.warning("Interrupted by user! Saving progress...")
            self._save_checkpoint()
            return

        logger.info("Waiting for all workers to complete...")
        task_queue.join()
        
        logger.info("All workers finished. Saving final sorted output...")
        self._save_final_output()

    def _save_final_output(self):
        logger.info("Reordering results to match input order...")
        ordered_results = []
        
        for p in self.input_products_data:
            pid = self._get_product_id(p)
            if pid and pid in self.enriched_products:
                ordered_results.append(self.enriched_products[pid])
            else:
                # Fallback
                ordered_results.append({**p, 'nutrition': {}, 'allergies': {}, 'ingredients': None})

        logger.info(f"Saving final enriched data to {self.output_file}...")
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(ordered_results, f, ensure_ascii=False, indent=2)

        logger.info(f"Successfully enriched {len(ordered_results)} products to {self.output_file}")

    @abstractmethod
    def get_product_info(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch nutrition, allergies, and ingredients for a single product.
        Returns a dict with 'nutrition', 'allergies', 'ingredients'.
        Should raise an Exception if fetching fails (to trigger retry logic).
        """
        pass

class EnricherWorker(threading.Thread):
    def __init__(self, task_queue: Queue, enricher: BaseProductEnricher, worker_id: int):
        super().__init__(daemon=True)
        self.task_queue = task_queue
        self.enricher = enricher
        self.worker_id = worker_id

    def run(self):
        while True:
            try:
                product = self.task_queue.get_nowait()
            except Empty:
                logger.debug(f"Worker {self.worker_id}: queue empty, finished")
                return

            identifier = self.enricher._get_product_id(product)
            
            # Exponential backoff state per item
            backoff = 1.0
            max_backoff = 60.0
            
            while True:
                try:
                    info = self.enricher.get_product_info(product)
                    enriched = {**product, **info}
                    
                    with self.enricher.results_lock:
                        self.enricher.enriched_products[identifier] = enriched
                        if len(self.enricher.enriched_products) % 50 == 0:
                            logger.info(f"Progress: {len(self.enricher.enriched_products)} products enriched")
                    break

                except Exception as e:
                    # If we detect HTTP 429 or 503 in the exception message, back off and retry.
                    msg = str(e).lower()
                    if '429' in msg or '503' in msg or 'rate' in msg or 'too many' in msg:
                        sleep_time = min(max_backoff, backoff)
                        logger.warning(f"Worker {self.worker_id}: rate limited or server error (429/503) when fetching {identifier}, sleeping {sleep_time}s and retrying")
                        time.sleep(sleep_time)
                        backoff *= 2
                        continue
                    else:
                        # Non-rate-limit error: record empty nutrition and move on
                        logger.warning(f"Worker {self.worker_id}: error fetching {identifier}: {e}")
                        enriched = {**product, 'nutrition': {}, 'allergies': {}, 'ingredients': None}
                        with self.enricher.results_lock:
                            self.enricher.enriched_products[identifier] = enriched
                        break

            self.task_queue.task_done()
