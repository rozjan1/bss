import json
import threading
import time
from queue import Queue, Empty
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from loguru import logger

class BaseProductEnricher(ABC):
    def __init__(self, input_file: str, output_file: str, num_workers: int = 8):
        self.input_file = input_file
        self.output_file = output_file
        self.num_workers = num_workers

    def enrich_products(self):
        logger.info(f"Loading products from {self.input_file}...")
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                products = json.load(f)
        except FileNotFoundError:
             logger.error(f"Input file {self.input_file} not found.")
             return

        logger.info(f"Found {len(products)} products to enrich")
        logger.info(f"Starting {self.num_workers} workers...")
        
        task_queue: Queue = Queue()
        for p in products:
            task_queue.put(p)

        results = []
        lock = threading.Lock()

        workers = [
            EnricherWorker(task_queue, results, lock, i, self) 
            for i in range(self.num_workers)
        ]
        for w in workers:
            w.start()

        logger.info("Waiting for all workers to complete...")
        task_queue.join()
        logger.info("All workers finished!")

        # Reordering results to match input order
        logger.info("Reordering results to match input order...")
        
        # Helper to get unique ID from product
        def get_id(p):
            return p.get('product_url') or p.get('url') or p.get('id')

        # Create a map of ID -> Enriched Product
        id_to_enriched = {}
        for r in results:
             pid = get_id(r)
             if pid:
                 id_to_enriched[pid] = r
        
        ordered_results = []
        for p in products:
            pid = get_id(p)
            if pid and pid in id_to_enriched:
                ordered_results.append(id_to_enriched[pid])
            else:
                # Fallback to original product + empty fields if something went wrong
                # (though worker usually appends even on error)
                ordered_results.append({**p, 'nutrition': {}, 'allergies': {}, 'ingredients': None})

        logger.info(f"Saving enriched data to {self.output_file}...")
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
    def __init__(self, task_queue: Queue, results: list, lock: threading.Lock, worker_id: int, enricher: BaseProductEnricher):
        super().__init__(daemon=True)
        self.task_queue = task_queue
        self.results = results
        self.lock = lock
        self.worker_id = worker_id
        self.enricher = enricher

    def run(self):
        while True:
            try:
                product = self.task_queue.get_nowait()
            except Empty:
                logger.debug(f"Worker {self.worker_id}: queue empty, finished")
                return

            identifier = product.get('product_url') or product.get('url') or product.get('id')
            
            # Exponential backoff state per item
            backoff = 1.0
            max_backoff = 60.0
            
            while True:
                try:
                    info = self.enricher.get_product_info(product)
                    enriched = {**product, **info}
                    with self.lock:
                        self.results.append(enriched)
                        if len(self.results) % 100 == 0:
                            logger.info(f"Progress: {len(self.results)} products enriched")
                    break

                except Exception as e:
                    # If we detect HTTP 429 in the exception message, back off and retry.
                    msg = str(e).lower()
                    if '429' in msg or 'rate' in msg or 'too many' in msg:
                        sleep_time = min(max_backoff, backoff)
                        logger.warning(f"Worker {self.worker_id}: rate limited when fetching {identifier}, sleeping {sleep_time}s and retrying")
                        time.sleep(sleep_time)
                        backoff *= 2
                        continue
                    else:
                        # Non-rate-limit error: record empty nutrition and move on
                        logger.warning(f"Worker {self.worker_id}: error fetching {identifier}: {e}")
                        enriched = {**product, 'nutrition': {}, 'allergies': {}, 'ingredients': None}
                        with self.lock:
                            self.results.append(enriched)
                        break

            self.task_queue.task_done()
