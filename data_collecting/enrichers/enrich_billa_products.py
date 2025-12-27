import json
import requests
import threading
import time
from queue import Queue, Empty
from typing import Dict, Any
from loguru import logger

INPUT_FILE = 'billa_products.json'
OUTPUT_FILE = 'billa_products_enriched.json'
NUM_WORKERS = 8

COOKIES = {
    'XSRF-TOKEN': '9438d651-5e76-45b3-ae10-f3531882e07e',
    'OptanonAlertBoxClosed': '2025-12-03T10:14:03.198Z',
    'jts-rw': '{"u":"1291176475684166985018"}',
    '_clck': '1w71g7t%5E2%5Eg1v%5E0%5E2163',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Mon+Dec+15+2025+11%3A31%3A36+GMT%2B0100+(Central+European+Standard+Time)&version=202510.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&genVendors=&consentId=bed1a886-4afa-4f63-8413-d365969d56a9&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A0%2CC0004%3A0&intType=2&geolocation=%3B&AwaitingReconsent=false',
    'jctr_sid': '46932176580361793767834',
    '_clsk': 'lt9s0x%5E1765803647627%5E7%5E1%5Ey.clarity.ms%2Fcollect',
    '_uetsid': '73cb2e80d99811f0b5ab1da802272ddc',
    '_uetvid': 'cff49a00d03011f087907952d7f53f2e',
}

HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'credentials': 'include',
    'priority': 'u=1, i',
    'referer': 'https://shop.billa.cz/produkt/jihoceska-niva-45-82351105',
    'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
    'x-request-id': '2d9d874b-6de1-4123-97b0-b2bd33cd8b36-1765794695485',
    'x-xsrf-token': '9438d651-5e76-45b3-ae10-f3531882e07e',
}

def extract_product_details(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and formats nutrition, allergies, and ingredients from the 
    Billa product detail JSON into the desired target structure.
    """
    logger.debug("Starting extract_product_details")

    # --- 1. Locate Necessary Nested Data ---
    
    # We look inside the first element of additionalInformation
    logger.debug("Extracting nested data...")
    additional_info = product_data.get("additionalInformation", [{}])
    logger.debug(f"additional_info has {len(additional_info)} items")
    
    food_info = additional_info[0].get("foodInformation", {})
    logger.debug(f"food_info keys: {list(food_info.keys())}")
    
    calculated_nutrition = food_info.get("calculatedNutrition", {})
    logger.debug(f"calculated_nutrition keys: {list(calculated_nutrition.keys())}")
    
    # --- 2. Extract NUTRITION Data ---
    
    logger.debug("Extracting nutrition data...")
    nutrition_output = {"Výživové údaje na": None}
    
    # Get the base unit (e.g., "100g")
    base_unit = calculated_nutrition.get("headers", {}).get("per100Header", "na 100g").replace("na ", "")
    nutrition_output["Výživové údaje na"] = base_unit.strip()
    logger.debug(f"Base unit: {base_unit.strip()}")

    # Process the list of nutrients
    nutrition_data = calculated_nutrition.get("data", [])
    logger.debug(f"Found {len(nutrition_data)} nutrition items")
    
    for item in nutrition_data:
        name = item.get("name", "").strip()
        value = item.get("valuePer100", "").strip()
        logger.debug(f"Processing nutrient - name: '{name}', value: '{value}'")

        if not name or not value:
            logger.debug("Skipping empty nutrient")
            continue
            
        try:
            num_value = float(value)
            logger.debug(f"Converted to float: {num_value}")
            
            # Map and format the nutrient name/value
            if name in ["KJ", "Energetická hodnota (kJ)"]:
                # Use integer formatting with space as thousands separator
                nutrition_output["Energetická hodnota kJ"] = f"{int(num_value):,} kJ".replace(",", " ")
            elif name in ["Kcal", "Energetická hodnota (kcal)"]:
                nutrition_output["Energetická hodnota kcal"] = f"{int(num_value):,} kcal".replace(",", " ")
            elif name in ["Tuky", "Tuky (g)"]:
                # Format to one decimal place, replacing the decimal point with a comma
                nutrition_output["Tuky"] = f"{num_value:.1f} g".replace(".", ",")
            elif name in ["Z toho nasycené mastné kyseliny", " z toho nasycené (g)"]:
                # Use integer or one decimal place based on value, replacing the decimal point with a comma
                format_str = f"{num_value:.0f} g" if num_value == int(num_value) else f"{num_value:.1f} g"
                nutrition_output["z toho nasycené mastné kyseliny"] = format_str.replace(".", ",")
            elif name in ["Sacharidy", "Sacharidy (g)"]:
                nutrition_output["Sacharidy"] = f"{num_value:.1f} g".replace(".", ",")
            elif name in ["Z toho cukry", " z toho cukry (g)"]:
                nutrition_output["z toho cukry"] = f"{num_value:.1f} g".replace(".", ",")
            elif name in ["Bílkoviny", "Bílkoviny (g)"]:
                # Use integer or one decimal place based on value, replacing the decimal point with a comma
                format_str = f"{num_value:.0f} g" if num_value == int(num_value) else f"{num_value:.1f} g"
                nutrition_output["Bílkoviny"] = format_str.replace(".", ",")
            elif name in ["Sůl", "Sůl (g)"]:
                # Format to two decimal places, replacing the decimal point with a comma
                nutrition_output["Sůl"] = f"{num_value:.2f} g".replace(".", ",")

        except ValueError as e:
            # Skip non-numeric values
            logger.debug(f"ValueError converting '{value}' to float: {e}")
            continue
    
    logger.debug(f"Nutrition output: {nutrition_output}")

    # --- 3. Extract ALLERGIES Data ---
    
    logger.debug("Extracting allergies data...")
    # In the Billa structure, 'allergens' or 'allergyAdvice' contains positive findings (Contains).
    # Since the JSON doesn't provide explicit 'May contain' or 'Does not contain' lists, 
    # we only populate the 'Obsahuje' (Contains) list.
    
    allergies_output = {
        "Obsahuje": [],
        "Může obsahovat": [],
        "Neobsahuje": []
        
    }
    
    # Use the top-level 'allergens' list if available
    top_level_allergens = product_data.get("allergens", [])
    logger.debug(f"Top-level allergens: {top_level_allergens}")
    
    # Or, use the nested 'allergyAdvice' list
    nested_allergens = [
        item.get("value1") for item in food_info.get("allergyAdvice", [])
    ]
    logger.debug(f"Nested allergens: {nested_allergens}")
    
    # Combine and clean the allergen list (capitalize first letter, remove duplicates)
    combined_allergens = set(
        [a.strip().capitalize() for a in top_level_allergens + nested_allergens if a]
    )
    logger.debug(f"Combined allergens: {combined_allergens}")
    
    # Split the list in half and only keep the second half (text-based allergens)
    sorted_allergens = sorted(list(combined_allergens))
    half_index = len(sorted_allergens) // 2
    allergies_output["Obsahuje"] = sorted_allergens[half_index:]
    logger.debug(f"Allergies output (second half only): {allergies_output}")
    
    # --- 4. Extract INGREDIENTS Data ---
    
    logger.debug("Extracting ingredients data...")
    # The ingredients are in 'foodInformation.ingredientsText'. We remove HTML tags (like <strong>)
    ingredients_text = food_info.get("ingredientsText", "")
    logger.debug(f"Raw ingredients text length: {len(ingredients_text)}")
    
    # Simple cleanup to remove bold tags 
    ingredients_text_cleaned = ingredients_text.replace("<strong>", "").replace("</strong>", "").strip()
    logger.debug(f"Cleaned ingredients preview: {ingredients_text_cleaned[:100]}...")

    # --- 5. Assemble Final Output ---
    
    logger.debug("Assembling final output...")
    final_output = {
        "nutrition": nutrition_output,
        "allergies": allergies_output,
        "ingredients": ingredients_text_cleaned
    }
    
    logger.debug("extract_product_details completed successfully")
    return final_output

class EnricherWorker(threading.Thread):
    """Worker thread for enriching Billa products in parallel."""
    
    def __init__(self, task_queue: Queue, results: list, lock: threading.Lock, worker_id: int):
        super().__init__(daemon=True)
        self.task_queue = task_queue
        self.results = results
        self.lock = lock
        self.worker_id = worker_id

    def run(self):
        while True:
            try:
                product = self.task_queue.get_nowait()
            except Empty:
                logger.info(f"Worker {self.worker_id}: finished")
                return

            product_url = product.get("product_url")
            
            # Skip products without URLs
            if not product_url:
                enriched = {**product, 'nutrition': {}, 'allergies': {}, 'ingredients': None}
                with self.lock:
                    self.results.append(enriched)
                self.task_queue.task_done()
                continue

            # Extract product ID from URL
            try:
                product_id = product_url.split("-")[-1]
                product_id = product_id[:2] + "-" + product_id[2:]
            except Exception as e:
                logger.warning(f"Worker {self.worker_id}: Could not extract product ID from {product_url}: {e}")
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
                    api_url = f"https://shop.billa.cz/api/product-discovery/products/{product_id}"
                    response = requests.get(api_url, cookies=COOKIES, headers=HEADERS, timeout=10)
                    
                    if response.status_code != 200:
                        logger.warning(f"Worker {self.worker_id}: Non-200 status ({response.status_code}) for {product_id}")
                        enriched = {**product, 'nutrition': {}, 'allergies': {}, 'ingredients': None}
                        with self.lock:
                            self.results.append(enriched)
                        break
                    
                    product_data = response.json()
                    extracted_details = extract_product_details(product_data)
                    enriched = {**product, **extracted_details}
                    
                    with self.lock:
                        self.results.append(enriched)
                        if len(self.results) % 100 == 0:
                            logger.info(f"Progress: {len(self.results)} products enriched")
                    break

                except Exception as e:
                    # If we detect HTTP 429 in the exception message, back off and retry
                    msg = str(e).lower()
                    if '429' in msg or 'rate' in msg or 'too many' in msg:
                        sleep_time = min(max_backoff, backoff)
                        logger.warning(f"Worker {self.worker_id}: rate limited for {product_id}, sleeping {sleep_time}s and retrying")
                        time.sleep(sleep_time)
                        backoff *= 2
                        continue
                    else:
                        # Non-rate-limit error: record empty enrichment and move on
                        logger.warning(f"Worker {self.worker_id}: error fetching {product_id}: {e}")
                        enriched = {**product, 'nutrition': {}, 'allergies': {}, 'ingredients': None}
                        with self.lock:
                            self.results.append(enriched)
                        break

            self.task_queue.task_done()


def enrich_products(input_path: str = INPUT_FILE, output_path: str = OUTPUT_FILE, num_workers: int = NUM_WORKERS):
    """Load products, enrich them using workers, and save results."""
    logger.info(f"Loading products from {input_path}...")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except Exception as e:
        logger.exception(f"Failed to load {input_path}: {e}")
        raise

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

    # Preserve input order by mapping results by product_url
    logger.info("Reordering results to match input order...")
    url_to_enriched = {r.get('product_url'): r for r in results}
    ordered_results = [url_to_enriched.get(p.get('product_url'), {**p, 'nutrition': {}, 'allergies': {}, 'ingredients': None}) for p in products]

    logger.info(f"Saving enriched data to {output_path}...")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(ordered_results, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.exception(f"Failed to write output file: {e}")
        raise

    logger.info(f"Successfully enriched {len(ordered_results)} products to {output_path}")


if __name__ == '__main__':
    enrich_products()
import json
import requests
import threading
import time
from queue import Queue, Empty
from typing import Dict, Any
from loguru import logger

INPUT_FILE = 'billa_products.json'
OUTPUT_FILE = 'billa_products_enriched.json'
NUM_WORKERS = 8

COOKIES = {
    'XSRF-TOKEN': '9438d651-5e76-45b3-ae10-f3531882e07e',
    'OptanonAlertBoxClosed': '2025-12-03T10:14:03.198Z',
    'jts-rw': '{"u":"1291176475684166985018"}',
    '_clck': '1w71g7t%5E2%5Eg1v%5E0%5E2163',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Mon+Dec+15+2025+11%3A31%3A36+GMT%2B0100+(Central+European+Standard+Time)&version=202510.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&genVendors=&consentId=bed1a886-4afa-4f63-8413-d365969d56a9&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A0%2CC0004%3A0&intType=2&geolocation=%3B&AwaitingReconsent=false',
    'jctr_sid': '46932176580361793767834',
    '_clsk': 'lt9s0x%5E1765803647627%5E7%5E1%5Ey.clarity.ms%2Fcollect',
    '_uetsid': '73cb2e80d99811f0b5ab1da802272ddc',
    '_uetvid': 'cff49a00d03011f087907952d7f53f2e',
}

HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'credentials': 'include',
    'priority': 'u=1, i',
    'referer': 'https://shop.billa.cz/produkt/jihoceska-niva-45-82351105',
    'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
    'x-request-id': '2d9d874b-6de1-4123-97b0-b2bd33cd8b36-1765794695485',
    'x-xsrf-token': '9438d651-5e76-45b3-ae10-f3531882e07e',
}

def extract_product_details(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and formats nutrition, allergies, and ingredients from the 
    Billa product detail JSON into the desired target structure.
    """
    logger.debug("Starting extract_product_details")

    # --- 1. Locate Necessary Nested Data ---
    
    # We look inside the first element of additionalInformation
    logger.debug("Extracting nested data...")
    additional_info = product_data.get("additionalInformation", [{}])
    logger.debug(f"additional_info has {len(additional_info)} items")
    
    food_info = additional_info[0].get("foodInformation", {})
    logger.debug(f"food_info keys: {list(food_info.keys())}")
    
    calculated_nutrition = food_info.get("calculatedNutrition", {})
    logger.debug(f"calculated_nutrition keys: {list(calculated_nutrition.keys())}")
    
    # --- 2. Extract NUTRITION Data ---
    
    logger.debug("Extracting nutrition data...")
    nutrition_output = {"Výživové údaje na": None}
    
    # Get the base unit (e.g., "100g")
    base_unit = calculated_nutrition.get("headers", {}).get("per100Header", "na 100g").replace("na ", "")
    nutrition_output["Výživové údaje na"] = base_unit.strip()
    logger.debug(f"Base unit: {base_unit.strip()}")

    # Process the list of nutrients
    nutrition_data = calculated_nutrition.get("data", [])
    logger.debug(f"Found {len(nutrition_data)} nutrition items")
    
    for item in nutrition_data:
        name = item.get("name", "").strip()
        value = item.get("valuePer100", "").strip()
        logger.debug(f"Processing nutrient - name: '{name}', value: '{value}'")

        if not name or not value:
            logger.debug("Skipping empty nutrient")
            continue
            
        try:
            num_value = float(value)
            logger.debug(f"Converted to float: {num_value}")
            
            # Map and format the nutrient name/value
            if name in ["KJ", "Energetická hodnota (kJ)"]:
                # Use integer formatting with space as thousands separator
                nutrition_output["Energetická hodnota kJ"] = f"{int(num_value):,} kJ".replace(",", " ")
            elif name in ["Kcal", "Energetická hodnota (kcal)"]:
                nutrition_output["Energetická hodnota kcal"] = f"{int(num_value):,} kcal".replace(",", " ")
            elif name in ["Tuky", "Tuky (g)"]:
                # Format to one decimal place, replacing the decimal point with a comma
                nutrition_output["Tuky"] = f"{num_value:.1f} g".replace(".", ",")
            elif name in ["Z toho nasycené mastné kyseliny", " z toho nasycené (g)"]:
                # Use integer or one decimal place based on value, replacing the decimal point with a comma
                format_str = f"{num_value:.0f} g" if num_value == int(num_value) else f"{num_value:.1f} g"
                nutrition_output["z toho nasycené mastné kyseliny"] = format_str.replace(".", ",")
            elif name in ["Sacharidy", "Sacharidy (g)"]:
                nutrition_output["Sacharidy"] = f"{num_value:.1f} g".replace(".", ",")
            elif name in ["Z toho cukry", " z toho cukry (g)"]:
                nutrition_output["z toho cukry"] = f"{num_value:.1f} g".replace(".", ",")
            elif name in ["Bílkoviny", "Bílkoviny (g)"]:
                # Use integer or one decimal place based on value, replacing the decimal point with a comma
                format_str = f"{num_value:.0f} g" if num_value == int(num_value) else f"{num_value:.1f} g"
                nutrition_output["Bílkoviny"] = format_str.replace(".", ",")
            elif name in ["Sůl", "Sůl (g)"]:
                # Format to two decimal places, replacing the decimal point with a comma
                nutrition_output["Sůl"] = f"{num_value:.2f} g".replace(".", ",")

        except ValueError as e:
            # Skip non-numeric values
            logger.debug(f"ValueError converting '{value}' to float: {e}")
            continue
    
    logger.debug(f"Nutrition output: {nutrition_output}")

    # --- 3. Extract ALLERGIES Data ---
    
    logger.debug("Extracting allergies data...")
    # In the Billa structure, 'allergens' or 'allergyAdvice' contains positive findings (Contains).
    # Since the JSON doesn't provide explicit 'May contain' or 'Does not contain' lists, 
    # we only populate the 'Obsahuje' (Contains) list.
    
    allergies_output = {
        "Obsahuje": [],
        "Neobsahuje": [],
        "Může obsahovat": [],
        "Inconnu": []
    }
    
    # Use the top-level 'allergens' list if available
    top_level_allergens = product_data.get("allergens", [])
    logger.debug(f"Top-level allergens: {top_level_allergens}")
    
    # Or, use the nested 'allergyAdvice' list
    nested_allergens = [
        item.get("value1") for item in food_info.get("allergyAdvice", [])
    ]
    logger.debug(f"Nested allergens: {nested_allergens}")
    
    # Combine and clean the allergen list (capitalize first letter, remove duplicates)
    combined_allergens = set(
        [a.strip().capitalize() for a in top_level_allergens + nested_allergens if a]
    )
    logger.debug(f"Combined allergens: {combined_allergens}")
    
    # Split the list in half and only keep the second half (text-based allergens)
    sorted_allergens = sorted(list(combined_allergens))
    half_index = len(sorted_allergens) // 2
    allergies_output["Obsahuje"] = sorted_allergens[half_index:]
    logger.debug(f"Allergies output (second half only): {allergies_output}")
    
    # --- 4. Extract INGREDIENTS Data ---
    
    logger.debug("Extracting ingredients data...")
    # The ingredients are in 'foodInformation.ingredientsText'. We remove HTML tags (like <strong>)
    ingredients_text = food_info.get("ingredientsText", "")
    logger.debug(f"Raw ingredients text length: {len(ingredients_text)}")
    
    # Simple cleanup to remove bold tags 
    ingredients_text_cleaned = ingredients_text.replace("<strong>", "").replace("</strong>", "").strip()
    logger.debug(f"Cleaned ingredients preview: {ingredients_text_cleaned[:100]}...")

    # --- 5. Assemble Final Output ---
    
    logger.debug("Assembling final output...")
    final_output = {
        "nutrition": nutrition_output,
        "allergies": allergies_output,
        "ingredients": ingredients_text_cleaned
    }
    
    logger.debug("extract_product_details completed successfully")
    return final_output

class EnricherWorker(threading.Thread):
    """Worker thread for enriching Billa products in parallel."""
    
    def __init__(self, task_queue: Queue, results: list, lock: threading.Lock, worker_id: int):
        super().__init__(daemon=True)
        self.task_queue = task_queue
        self.results = results
        self.lock = lock
        self.worker_id = worker_id

    def run(self):
        while True:
            try:
                product = self.task_queue.get_nowait()
            except Empty:
                logger.info(f"Worker {self.worker_id}: finished")
                return

            product_url = product.get("product_url")
            
            # Skip products without URLs
            if not product_url:
                enriched = {**product, 'nutrition': {}, 'allergies': {}, 'ingredients': None}
                with self.lock:
                    self.results.append(enriched)
                self.task_queue.task_done()
                continue

            # Extract product ID from URL
            try:
                product_id = product_url.split("-")[-1]
                product_id = product_id[:2] + "-" + product_id[2:]
            except Exception as e:
                logger.warning(f"Worker {self.worker_id}: Could not extract product ID from {product_url}: {e}")
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
                    api_url = f"https://shop.billa.cz/api/product-discovery/products/{product_id}"
                    response = requests.get(api_url, cookies=COOKIES, headers=HEADERS, timeout=10)
                    
                    if response.status_code != 200:
                        logger.warning(f"Worker {self.worker_id}: Non-200 status ({response.status_code}) for {product_id}")
                        enriched = {**product, 'nutrition': {}, 'allergies': {}, 'ingredients': None}
                        with self.lock:
                            self.results.append(enriched)
                        break
                    
                    product_data = response.json()
                    extracted_details = extract_product_details(product_data)
                    enriched = {**product, **extracted_details}
                    
                    with self.lock:
                        self.results.append(enriched)
                        if len(self.results) % 100 == 0:
                            logger.info(f"Progress: {len(self.results)} products enriched")
                    break

                except Exception as e:
                    # If we detect HTTP 429 in the exception message, back off and retry
                    msg = str(e).lower()
                    if '429' in msg or 'rate' in msg or 'too many' in msg:
                        sleep_time = min(max_backoff, backoff)
                        logger.warning(f"Worker {self.worker_id}: rate limited for {product_id}, sleeping {sleep_time}s and retrying")
                        time.sleep(sleep_time)
                        backoff *= 2
                        continue
                    else:
                        # Non-rate-limit error: record empty enrichment and move on
                        logger.warning(f"Worker {self.worker_id}: error fetching {product_id}: {e}")
                        enriched = {**product, 'nutrition': {}, 'allergies': {}, 'ingredients': None}
                        with self.lock:
                            self.results.append(enriched)
                        break

            self.task_queue.task_done()


def enrich_products(input_path: str = INPUT_FILE, output_path: str = OUTPUT_FILE, num_workers: int = NUM_WORKERS):
    """Load products, enrich them using workers, and save results."""
    logger.info(f"Loading products from {input_path}...")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
    except Exception as e:
        logger.exception(f"Failed to load {input_path}: {e}")
        raise

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

    # Preserve input order by mapping results by product_url
    logger.info("Reordering results to match input order...")
    url_to_enriched = {r.get('product_url'): r for r in results}
    ordered_results = [url_to_enriched.get(p.get('product_url'), {**p, 'nutrition': {}, 'allergies': {}, 'ingredients': None}) for p in products]

    logger.info(f"Saving enriched data to {output_path}...")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(ordered_results, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.exception(f"Failed to write output file: {e}")
        raise

    logger.info(f"Successfully enriched {len(ordered_results)} products to {output_path}")


if __name__ == '__main__':
    enrich_products()