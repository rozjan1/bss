import json
import requests
import time
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Renaming the helper function for clarity in its purpose
def extract_product_details(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and formats nutrition, allergies, and ingredients from the 
    Billa product detail JSON into the desired target structure.
    """
    print("\n" + "="*60)

    # --- 1. Locate Necessary Nested Data ---
    
    # We look inside the first element of additionalInformation
    additional_info = product_data.get("additionalInformation", [{}])    
    food_info = additional_info[0].get("foodInformation", {})
    print(f"DEBUG: food_info keys: {list(food_info.keys())}")
    
    calculated_nutrition = food_info.get("calculatedNutrition", {})
    
    # --- 2. Extract NUTRITION Data ---
    nutrition_output = {"Výživové údaje na": None}
    
    # Get the base unit (e.g., "100g")
    base_unit = calculated_nutrition.get("headers", {}).get("per100Header", "na 100g").replace("na ", "")
    nutrition_output["Výživové údaje na"] = base_unit.strip()
    print(f"DEBUG: Base unit: {base_unit.strip()}")

    # Process the list of nutrients
    nutrition_data = calculated_nutrition.get("data", [])
    
    for item in nutrition_data:
        name = item.get("name", "").strip()
        value = item.get("valuePer100", "").strip()
        print(f"DEBUG: Processing nutrient - name: '{name}', value: '{value}'")

        if not name or not value:
            print(f"DEBUG: Skipping empty nutrient")
            continue
            
        try:
            num_value = float(value)
            
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
            print(f"DEBUG: ValueError converting '{value}' to float: {e}")
            continue
    
    print(f"DEBUG: Nutrition output: {nutrition_output}")

    # --- 3. Extract ALLERGIES Data ---
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
    print(f"DEBUG: Top-level allergens: {top_level_allergens}")
    
    # Or, use the nested 'allergyAdvice' list
    nested_allergens = [
        item.get("value1") for item in food_info.get("allergyAdvice", [])
    ]    
    # Combine and clean the allergen list (capitalize first letter, remove duplicates)
    combined_allergens = set(
        [a.strip().capitalize() for a in top_level_allergens + nested_allergens if a]
    )
    
    # Filter out entries that contain only numbers and spaces (like "1 112", "2 119")
    def is_only_numbers_and_spaces(s):
        """Check if string contains only digits and spaces"""
        return all(c.isdigit() or c.isspace() for c in s)
    
    text_based_allergens = [
        allergen for allergen in combined_allergens 
        if not is_only_numbers_and_spaces(allergen)
    ]
    
    allergies_output["Obsahuje"] = sorted(text_based_allergens)
    print(f"DEBUG: Filtered allergens (text only): {allergies_output['Obsahuje']}")
    
    # --- 4. Extract INGREDIENTS Data ---
    
    # The ingredients are in 'foodInformation.ingredientsText'. We remove HTML tags (like <strong>)
    ingredients_text = food_info.get("ingredientsText", "")
    
    # Simple cleanup to remove bold tags 
    ingredients_text_cleaned = ingredients_text.replace("<strong>", "").replace("</strong>", "").strip()

    # --- 5. Assemble Final Output ---
    final_output = {
        "nutrition": nutrition_output,
        "allergies": allergies_output,
        "ingredients": ingredients_text_cleaned
    }
    
    print("="*60 + "\n")
    return final_output

cookies = {
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

headers = {
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
    # 'cookie': 'XSRF-TOKEN=9438d651-5e76-45b3-ae10-f3531882e07e; OptanonAlertBoxClosed=2025-12-03T10:14:03.198Z; jts-rw={"u":"1291176475684166985018"}; _clck=1w71g7t%5E2%5Eg1v%5E0%5E2163; OptanonConsent=isGpcEnabled=0&datestamp=Mon+Dec+15+2025+11%3A31%3A36+GMT%2B0100+(Central+European+Standard+Time)&version=202510.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&genVendors=&consentId=bed1a886-4afa-4f63-8413-d365969d56a9&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A0%2CC0004%3A0&intType=2&geolocation=%3B&AwaitingReconsent=false; jctr_sid=46932176580361793767834; _clsk=lt9s0x%5E1765803647627%5E7%5E1%5Ey.clarity.ms%2Fcollect; _uetsid=73cb2e80d99811f0b5ab1da802272ddc; _uetvid=cff49a00d03011f087907952d7f53f2e',
}


def fetch_product_with_retry(product: Dict[str, Any], idx: int, total: int, max_retries: int = 5) -> Dict[str, Any]:
    """
    Fetches product details with retry logic and exponential backoff for rate limiting.
    """
    product_url = product.get("product_url")
    product_id = product_url.split("-")[-1]
    product_id = product_id[:2] + "-" + product_id[2:]  
    
    api_url = f"https://shop.billa.cz/api/product-discovery/products/{product_id}"
    
    for attempt in range(max_retries):
        try:
            print(f"[{idx}/{total}] Fetching product (attempt {attempt + 1}/{max_retries}): {product.get('item_name', 'Unknown')[:50]}")
            
            response = requests.get(api_url, cookies=cookies, headers=headers, timeout=10)
            
            # Handle rate limiting
            if response.status_code == 429:
                wait_time = (2 ** attempt) * 2  # Exponential backoff: 2, 4, 8, 16, 32 seconds
                print(f"[{idx}/{total}] Rate limited! Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            
            # Handle other non-200 responses
            if response.status_code != 200:
                print(f"[{idx}/{total}] WARNING: Status {response.status_code} for product {product_id}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"[{idx}/{total}] Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"[{idx}/{total}] Failed after {max_retries} attempts")
                    return None
            
            product_data = response.json()
            extracted_details = extract_product_details(product_data)
            
            # Merge the original product data with extracted details
            enriched_product = {**product, **extracted_details}
            print(f"[{idx}/{total}] ✓ Success")
            return enriched_product
            
        except requests.exceptions.Timeout:
            print(f"[{idx}/{total}] Timeout error, retrying...")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                print(f"[{idx}/{total}] Failed due to timeout after {max_retries} attempts")
                return None
                
        except Exception as e:
            print(f"[{idx}/{total}] ERROR: {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                return None
    
    return None


print("Starting main script...")
print("Loading products from billa_products.json...")

try:
    with open("billa_products.json") as f:
        products = json.load(f)
    print(f"Loaded {len(products)} products")
except Exception as e:
    print(f"ERROR: Failed to load billa_products.json: {e}")
    raise

# Thread-safe list and lock
enriched_products = []
results_lock = Lock()

# Number of concurrent threads
MAX_WORKERS = 8

print(f"\nStarting parallel processing with {MAX_WORKERS} workers...")
print("="*60)

start_time = time.time()

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    # Submit all tasks
    future_to_product = {
        executor.submit(fetch_product_with_retry, product, idx, len(products)): product 
        for idx, product in enumerate(products, 1)
    }
    
    # Process completed tasks
    for future in as_completed(future_to_product):
        result = future.result()
        if result:
            with results_lock:
                enriched_products.append(result)

elapsed_time = time.time() - start_time

print(f"\n{'='*60}")
print(f"Processed {len(enriched_products)}/{len(products)} products successfully")
print(f"Time elapsed: {elapsed_time:.2f} seconds")
print(f"Average time per product: {elapsed_time/len(products):.2f} seconds")
print(f"Writing results to billa_product_details.json...")

try:
    with open("billa_product_details.json", "w", encoding="utf-8") as f:
        json.dump(enriched_products, f, ensure_ascii=False, indent=2)
    print("Successfully wrote results to file")
except Exception as e:
    print(f"ERROR: Failed to write output file: {e}")
    raise

print("Script completed successfully!")
print(f"{'='*60}")