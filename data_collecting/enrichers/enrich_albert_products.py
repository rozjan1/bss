import json
import threading
import time
from queue import Queue, Empty
from typing import Dict, Any
from loguru import logger

from albert_get_product_info import AlbertProductInfoFetcher

INPUT_FILE = 'albert_products.json'
OUTPUT_FILE = 'albert_products_enriched.json'
NUM_WORKERS = 8

# Per-thread worker that fetches nutrition/allergy info and attaches it to the product record.
class EnricherWorker(threading.Thread):
    def __init__(self, task_queue: Queue, results: list, lock: threading.Lock, worker_id: int):
        super().__init__(daemon=True)
        self.task_queue = task_queue
        self.results = results
        self.lock = lock
        self.fetcher = AlbertProductInfoFetcher()
        self.worker_id = worker_id

    def run(self):
        while True:
            try:
                product = self.task_queue.get_nowait()
            except Empty:
                logger.info(f"Worker {self.worker_id}: finished")
                return

            url = product.get('product_url') or product.get('url')
            # Some items may not have a URL; skip them gracefully
            if not url:
                logger.warning(f"Worker {self.worker_id}: {product.get('name', 'Unknown product')} missing URL, skipping enrichment")
                enriched = {**product, 'nutrition': {}, 'allergies': {}, 'ingredients': None}
                with self.lock:
                    self.results.append(enriched)
                self.task_queue.task_done()
                continue

            # Exponential backoff state per item
            backoff = 1.0
            max_backoff = 60.0
            while True:
                try:
                    info = self.fetcher.fetch(url)
                    # attach the fetched info to the product
                    enriched = {**product, 'nutrition': info.get('nutrients', {}), 'allergies': info.get('allergies', {}), 'ingredients': info.get('ingredients')}
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
                        logger.warning(f"Worker {self.worker_id}: rate limited when fetching {url}, sleeping {sleep_time}s and retrying")
                        time.sleep(sleep_time)
                        backoff *= 2
                        continue
                    else:
                        # Non-rate-limit error: record empty nutrition and move on
                        logger.warning(f"Worker {self.worker_id}: error fetching {url}: {e}")
                        enriched = {**product, 'nutrition': {}, 'allergies': {}, 'ingredients': None}
                        with self.lock:
                            self.results.append(enriched)
                        break

            self.task_queue.task_done()


def enrich_products(input_path: str = INPUT_FILE, output_path: str = OUTPUT_FILE, num_workers: int = NUM_WORKERS):
    logger.info(f"Loading products from {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    logger.info(f"Found {len(products)} products to enrich")
    logger.info(f"Starting {num_workers} workers...")
    
    task_queue: Queue = Queue()
    for p in products:
        task_queue.put(p)

    results = []
    lock = threading.Lock()

    workers = [EnricherWorker(task_queue, results, lock, i) for i in range(num_workers)]
    for w in workers:
        w.start()

    # Wait for all tasks to finish
    logger.info("Waiting for all workers to complete...")
    task_queue.join()
    logger.info("All workers finished!")

    # Save results in the same input order if possible (we appended as completed order)
    # To preserve order, map by product identifier if available. We'll try to keep original order
    # by matching product_url field.
    logger.info("Reordering results to match input order...")
    url_to_enriched = {r.get('product_url') or r.get('url'): r for r in results}
    ordered_results = [url_to_enriched.get(p.get('product_url') or p.get('url'), {**p, 'nutrition': {}, 'allergies': {}, 'ingredients': None}) for p in products]

    logger.info(f"Saving enriched data to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ordered_results, f, ensure_ascii=False, indent=2)

    logger.info(f"Successfully enriched {len(ordered_results)} products to {output_path}")


if __name__ == '__main__':
    enrich_products()
