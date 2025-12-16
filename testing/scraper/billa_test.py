import requests
import json
from time import sleep
from typing import Dict, Any

def get_billa_data(billa_data):
    """
    Transforms product data from the Billa eshop format to a unified structure.

    Args:
        billa_data (dict): The input JSON data from Billa.

    Returns:
        list: A list of dictionaries, each representing a product in the target format.
    """
    transformed_products = []

    print("Amount of products in category:", billa_data.get("total", []))

    # The input structure is assumed to be a dictionary with a 'results' key
    results = billa_data.get("results", [])

    for product in results:
        # 1. Product Name and URL Slug
        item_name = product.get("name")
        product_slug = product.get("slug")
        product_id = product.get("productId")

        # 2. Category: Extract the highest level category name
        parent_categories = product.get("parentCategories", [[]])
        product_category = parent_categories[0][0].get("name", "Neznámá kategorie")
        
        # 3. Image URL: Use the first image in the list
        images = product.get("images", [])
        image_url = images[0] if images else None

        # 4. Pricing and Units
        price_data = product.get("price", {})
        regular_price_data = price_data.get("regular", {})
        loyalty_price_data = price_data.get("loyalty", {})

        # Original Price (Regular Price)
        # Billa stores price in cents/haléře, so divide by 100 to get CZK
        original_price_cents = regular_price_data.get("value")
        original_price = original_price_cents / 100 if original_price_cents is not None else None
        
        # Sale Price and Sale Requirement
        sale_price = original_price
        sale_ppu = None
        sale_requirement = None

        if loyalty_price_data:
            # If there is a 'loyalty' price, it means it's the sale price
            sale_price_cents = loyalty_price_data.get("value")
            sale_price = sale_price_cents / 100 if sale_price_cents is not None else original_price
            
            # The sale requirement is implied to be a loyalty card (Billa Card)
            sale_requirement = "Billa Card"

        # Sale Price Per Unit (PPU)
        # Use the loyalty PPU if available, otherwise use the regular PPU
        ppu_cents = loyalty_price_data.get("perStandardizedQuantity")
        if ppu_cents is None:
             ppu_cents = regular_price_data.get("perStandardizedQuantity")
        
        sale_ppu = ppu_cents / 100 if ppu_cents is not None else None

        # Unit Code: Use the baseUnitLong for the unit_code
        unit_code = price_data.get("baseUnitLong", "").lower()
        
        # 5. Product URL: Construct the URL (this is an educated guess based on the Albert example)
        # Format: https://www.billa.cz/shop/<category_slug>/<item_slug>/p/<product_id>
        # Note: Billa's actual shop URLs might be more complex, but this pattern is common for e-commerce.
        # Here we use the slug from the highest category and the item's slug.
        category_slug = parent_categories[0][0].get("slug", "neznamo")
        # In the Albert example, they used the category path: /Ovoce-a-zelenina/Ovoce/Banany-a-exoticke-ovoce/Banany/p/...
        # Let's try to mimic the multi-level structure if possible:
        url_path_parts = [p.get("slug") for p in parent_categories[0]]
        
        # We need the full category path for a realistic URL construction
        # Example: /Ovoce-a-zelenina/Ovoce/Banany/p/product_id
        full_category_path = "/".join(url_path_parts)
        
        product_url = f"https://shop.billa.cz/produkt/{product_slug}"

        # 6. Assemble the final item dictionary
        transformed_item = {
            "source": "billa",
            "product_category": product_category,
            "item_name": item_name,
            "image_url": image_url,
            "original_price": original_price,
            "sale_price": sale_price,
            "sale_ppu": sale_ppu,
            "unit_code": unit_code,
            "product_url": product_url,
            "sale_requirement": sale_requirement
        }
        
        transformed_products.append(transformed_item)

    return transformed_products

cookies = {
    'XSRF-TOKEN': '9438d651-5e76-45b3-ae10-f3531882e07e',
    'OptanonAlertBoxClosed': '2025-12-03T10:14:03.198Z',
    'jts-rw': '{"u":"1291176475684166985018"}',
    'jctr_sid': '18596176544678364134515',
    '_clck': '1w71g7t%5E2%5Eg1r%5E0%5E2163',
    '_uetsid': '4a75b700d67711f0857edbd92a190a95',
    '_uetvid': 'cff49a00d03011f087907952d7f53f2e',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Thu+Dec+11+2025+10%3A57%3A37+GMT%2B0100+(Central+European+Standard+Time)&version=202510.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&genVendors=&consentId=bed1a886-4afa-4f63-8413-d365969d56a9&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A0%2CC0004%3A0&intType=2&geolocation=%3B&AwaitingReconsent=false',
    '_clsk': '1641g7l%5E1765447903945%5E5%5E1%5Ey.clarity.ms%2Fcollect',
}

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9',
    'credentials': 'include',
    'priority': 'u=1, i',
    'referer': 'https://shop.billa.cz/produkty/ovoce-a-zelenina-1165?page=2',
    'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
    'x-request-id': '516d1d45-f11d-4db1-9364-5d2fc43a5c56-1765446810341',
    'x-xsrf-token': '9438d651-5e76-45b3-ae10-f3531882e07e',
    # 'cookie': 'XSRF-TOKEN=9438d651-5e76-45b3-ae10-f3531882e07e; OptanonAlertBoxClosed=2025-12-03T10:14:03.198Z; jts-rw={"u":"1291176475684166985018"}; jctr_sid=18596176544678364134515; _clck=1w71g7t%5E2%5Eg1r%5E0%5E2163; _uetsid=4a75b700d67711f0857edbd92a190a95; _uetvid=cff49a00d03011f087907952d7f53f2e; OptanonConsent=isGpcEnabled=0&datestamp=Thu+Dec+11+2025+10%3A57%3A37+GMT%2B0100+(Central+European+Standard+Time)&version=202510.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&genVendors=&consentId=bed1a886-4afa-4f63-8413-d365969d56a9&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A0%2CC0004%3A0&intType=2&geolocation=%3B&AwaitingReconsent=false; _clsk=1641g7l%5E1765447903945%5E5%5E1%5Ey.clarity.ms%2Fcollect',
}

categories = [
    "ovoce-a-zelenina-1165",
    "pecivo-1198",
    "chlazene-mlecne-a-rostlinne-vyrobky-1207",
    "maso-a-ryby-1263",
    "uzeniny-lahudky-a-hotova-jidla-1276",
    "mrazene-1307",
    "trvanlive-potraviny-1332",
    "cukrovinky-1449",
    "napoje-1474",
    "specialni-a-rostlinna-vyziva-1576"
]

all_products = []

# Paginate per category similarly to albert_test.py: try pages until empty results
for category in categories:
    print(f"Fetching category: {category}")
    for page_index in range(0, 500):  # large upper bound; we'll break when no results
        print(f"Fetching category {category}, page {page_index}")
        # copy params and set current page
        this_params = {
            'page': str(page_index),
            'sortBy': 'relevance',
            'enableStatistics': 'false',
            'enablePersonalization': 'false',
            'pageSize': '500',
        }

        try:
            response = requests.get(
                f'https://shop.billa.cz/api/product-discovery/categories/{category}/products',
                params=this_params,
                cookies=cookies,
                headers=headers,
                timeout=15,
            )
        except Exception as e:
            print(f"Request failed for category {category} page {page_index}: {e}")
            break

        try:
            data = response.json()
        except Exception as e:
            print(f"Failed to parse JSON for category {category} page {page_index}: {e}")
            break

        results = data.get('results', [])
        if not results:
            print(f"No more products for category {category} at page {page_index}. Stopping pagination.")
            break

        all_products.extend(get_billa_data(data))
        sleep(0.1)

with open('billa_products.json', 'w', encoding='utf-8') as f:
    json.dump(all_products, f, ensure_ascii=False, indent=2)
print("Billa product amount:", len(all_products))