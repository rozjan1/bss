import json
import requests
from typing import Dict, Any

# Renaming the helper function for clarity in its purpose
def extract_product_details(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts and formats nutrition, allergies, and ingredients from the 
    Billa product detail JSON into the desired target structure.
    """
    print("\n" + "="*60)
    print("DEBUG: Starting extract_product_details")
    print("="*60)
    
    # --- 1. Locate Necessary Nested Data ---
    
    # We look inside the first element of additionalInformation
    print("DEBUG: Extracting nested data...")
    additional_info = product_data.get("additionalInformation", [{}])
    print(f"DEBUG: additional_info has {len(additional_info)} items")
    
    food_info = additional_info[0].get("foodInformation", {})
    print(f"DEBUG: food_info keys: {list(food_info.keys())}")
    
    calculated_nutrition = food_info.get("calculatedNutrition", {})
    print(f"DEBUG: calculated_nutrition keys: {list(calculated_nutrition.keys())}")
    
    # --- 2. Extract NUTRITION Data ---
    
    print("\nDEBUG: Extracting nutrition data...")
    nutrition_output = {"Výživové údaje na": None}
    
    # Get the base unit (e.g., "100g")
    base_unit = calculated_nutrition.get("headers", {}).get("per100Header", "na 100g").replace("na ", "")
    nutrition_output["Výživové údaje na"] = base_unit.strip()
    print(f"DEBUG: Base unit: {base_unit.strip()}")

    # Process the list of nutrients
    nutrition_data = calculated_nutrition.get("data", [])
    print(f"DEBUG: Found {len(nutrition_data)} nutrition items")
    
    for item in nutrition_data:
        name = item.get("name", "").strip()
        value = item.get("valuePer100", "").strip()
        print(f"DEBUG: Processing nutrient - name: '{name}', value: '{value}'")

        if not name or not value:
            print(f"DEBUG: Skipping empty nutrient")
            continue
            
        try:
            num_value = float(value)
            print(f"DEBUG: Converted to float: {num_value}")
            
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
    
    print("\nDEBUG: Extracting allergies data...")
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
    print(f"DEBUG: Nested allergens: {nested_allergens}")
    
    # Combine and clean the allergen list (capitalize first letter, remove duplicates)
    combined_allergens = set(
        [a.strip().capitalize() for a in top_level_allergens + nested_allergens if a]
    )
    print(f"DEBUG: Combined allergens: {combined_allergens}")
    
    # Split the list in half and only keep the second half (text-based allergens)
    sorted_allergens = sorted(list(combined_allergens))
    half_index = len(sorted_allergens) // 2
    allergies_output["Obsahuje"] = sorted_allergens[half_index:]
    print(f"DEBUG: Allergies output (second half only): {allergies_output}")
    
    # --- 4. Extract INGREDIENTS Data ---
    
    print("\nDEBUG: Extracting ingredients data...")
    # The ingredients are in 'foodInformation.ingredientsText'. We remove HTML tags (like <strong>)
    ingredients_text = food_info.get("ingredientsText", "")
    print(f"DEBUG: Raw ingredients text length: {len(ingredients_text)}")
    
    # Simple cleanup to remove bold tags 
    ingredients_text_cleaned = ingredients_text.replace("<strong>", "").replace("</strong>", "").strip()
    print(f"DEBUG: Cleaned ingredients preview: {ingredients_text_cleaned[:100]}...")

    # --- 5. Assemble Final Output ---
    
    print("\nDEBUG: Assembling final output...")
    final_output = {
        "nutrition": nutrition_output,
        "allergies": allergies_output,
        "ingredients": ingredients_text_cleaned
    }
    
    print("DEBUG: extract_product_details completed successfully")
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


print("Starting main script...")
print("Loading products from billa_products.json...")

try:
    with open("billa_products.json") as f:
        products = json.load(f)
    print(f"Loaded {len(products)} products")
except Exception as e:
    print(f"ERROR: Failed to load billa_products.json: {e}")
    raise

product_details = []
for idx, product in enumerate(products, 1):
    try:
        print(f"\n{'='*60}")
        print(f"Processing product {idx}/{len(products)}")
        print(f"{'='*60}")
        
        product_url = product.get("product_url")
        print(f"Product URL: {product_url}")
        
        product_id = product_url.split("-")[-1]
        product_id = product_id[:2] + "-" + product_id[2:]  
        print(f"Product ID: {product_id}")
        
        api_url = f"https://shop.billa.cz/api/product-discovery/products/{product_id}"
        print(f"Fetching from: {api_url}")
        
        response = requests.get(api_url, cookies=cookies, headers=headers)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"WARNING: Non-200 status code for product {product_id}")
            print(f"Response text: {response.text[:200]}")
            continue
        
        product_data = response.json()
        print(f"Successfully parsed JSON response")
        
        extracted_details = extract_product_details(product_data)
        product_details.append(extracted_details)
        print(f"Product {idx} processed successfully")
        
    except Exception as e:
        print(f"ERROR: Failed to process product {idx}")
        print(f"Product URL: {product.get('product_url', 'N/A')}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        continue

print(f"\n{'='*60}")
print(f"Processed {len(product_details)} products successfully")
print(f"Writing results to billa_product_details.json...")

try:
    with open("billa_product_details.json", "w", encoding="utf-8") as f:
        json.dump(product_details, f, ensure_ascii=False, indent=2)
    print("Successfully wrote results to file")
except Exception as e:
    print(f"ERROR: Failed to write output file: {e}")
    raise

print("Script completed successfully!")
print(f"{'='*60}")