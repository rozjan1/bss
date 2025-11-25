import requests
import csv
import time

# ========== CONFIG ==========
API_URL = "https://xapi.tesco.com/"
HEADERS = {
    "x-apikey": "TvOSZJHlEk0pjniDGQFAc9Q59WGAR4dA",
    "region": "CZ",
    "language": "cs-CZ",
    "content-type": "application/json",
    "user-agent": "Mozilla/5.0 (compatible; TescoScraper/1.0)",
}
CSV_FILE = "tesco_products.csv"
REQUEST_DELAY = 1.5  # seconds between pages
# ============================


def fetch_category_facets():
    """Fetch the root 'groceries' category and extract subcategory facets."""
    payload = [
        {
            "operationName": "GetCategoryProducts",
            "variables": {
                "page": 1,
                "count": 24,
                "facet": "b;groceries",
                "filterCriteria": [{"name": "0", "values": ["groceries"]}],
                "sortBy": "relevance",
            },
            "query": "query GetCategoryProducts($page:Int,$count:Int,$facet:String,$filterCriteria:[FilterCriterionInput!],$sortBy:String){category(facet:$facet){facetLists{facets{facetId,facetName}}}}",
        }
    ]

    r = requests.post(API_URL, headers=HEADERS, json=payload)
    print("Status code:", r.status_code)
    try:
        data = r.json()
        print("Response keys:", data[0].keys() if isinstance(data, list) else data.keys())
        print("\n--- RAW JSON SAMPLE ---\n", data if isinstance(data, dict) else data[0])
    except Exception as e:
        print("Could not decode JSON:", e)
        print("Raw text:", r.text[:500])
    exit()  # Stop here to just inspect response once



def fetch_products_from_category(facet_id, category_name):
    """Fetch all products for a given category facet."""
    page = 1
    all_products = []

    while True:
        payload = [
            {
                "operationName": "GetCategoryProducts",
                "variables": {
                    "page": page,
                    "count": 48,
                    "facet": facet_id,
                    "filterCriteria": [{"name": "0", "values": ["groceries"]}],
                    "sortBy": "relevance",
                },
                "query": """query GetCategoryProducts($page:Int,$count:Int,$facet:String,$filterCriteria:[FilterCriterionInput!],$sortBy:String){
                    category(facet:$facet){
                        products(page:$page,count:$count,filterCriteria:$filterCriteria,sortBy:$sortBy){
                            id
                            title
                            brand
                            price{
                                unit
                                value
                            }
                            gtin
                            quantity
                            imageUrl
                        }
                    }
                }""",
            }
        ]

        r = requests.post(API_URL, headers=HEADERS, json=payload)
        r.raise_for_status()
        data = r.json()

        try:
            products = data[0]["data"]["category"]["products"]
        except (KeyError, TypeError):
            break

        if not products:
            break

        for p in products:
            all_products.append({
                "category": category_name,
                "title": p.get("title"),
                "brand": p.get("brand"),
                "price_value": p.get("price", {}).get("value"),
                "price_unit": p.get("price", {}).get("unit"),
                "gtin": p.get("gtin"),
                "quantity": p.get("quantity"),
                "image_url": p.get("imageUrl"),
            })

        print(f"[{category_name}] Page {page} -> {len(products)} items")
        page += 1
        time.sleep(REQUEST_DELAY)

    return all_products


def main():
    print("🔍 Fetching Tesco.cz category list...")
    categories = fetch_category_facets()
    print(f"Found {len(categories)} categories:")
    for name in categories:
        print(" -", name)

    all_data = []

    for category_name, facet_id in categories.items():
        print(f"\n📦 Scraping category: {category_name}")
        products = fetch_products_from_category(facet_id, category_name)
        all_data.extend(products)
        print(f"✅ {len(products)} items scraped from {category_name}\n")

    # Save all to CSV
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_data[0].keys())
        writer.writeheader()
        writer.writerows(all_data)

    print(f"\n🎉 Done! Saved {len(all_data)} products to {CSV_FILE}")


if __name__ == "__main__":
    main()
