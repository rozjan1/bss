from camoufox.sync_api import Camoufox
import time
import random

def scrape_product_details(url):
    with Camoufox(headless=True, geoip=True) as browser:
        page = browser.new_page()
        
        print(f"Navigating to: {url}")
        page.goto(url)
        time.sleep(random.uniform(2, 4))
        
        product_data = {}

        # 1. Get Basic Info (Title & Price)
        try:
            product_data['title'] = page.locator("h1").first.inner_text().strip()
            # Try to find price
            # Updated selector for BuyBox price
            price_loc = page.locator(".ddsweb-buybox__price p.ddsweb-text").first
            if price_loc.is_visible():
                product_data['price'] = price_loc.inner_text().strip()
        except:
            pass

        # 2. Extract Accordion Data (Description, Storage, Nutrition, etc.)
        # We target the stable 'data-testid' attributes
        accordion_items = page.locator('[data-testid="accordion-item"]').all()
        
        print(f"Found {len(accordion_items)} information sections.")

        for item in accordion_items:
            try:
                # Extract the Header (e.g., "Popis produktu", "Výživové hodnoty")
                header_btn = item.locator('[data-testid="accordion-control"]')
                section_title = header_btn.inner_text().strip()
                
                # If the section is closed, click it to load content (just in case)
                if item.get_attribute("class") and "expanded" not in item.get_attribute("class"):
                    header_btn.click()
                    time.sleep(0.5)

                # Extract the Content Panel
                panel = item.locator('[data-testid="accordion-panel"]')
                
                # Check if this is a Nutrition Table (contains <table>)
                if panel.locator("table").count() > 0:
                    # Parse Nutrition Table specifically
                    nutrition_dict = {}
                    rows = panel.locator("tr").all()
                    for row in rows:
                        cols = row.locator("td, th").all_inner_texts()
                        if len(cols) >= 2:
                            # Key: Value (e.g., "Energy": "100kJ")
                            nutrition_dict[cols[0].strip()] = cols[1].strip()
                    product_data[section_title] = nutrition_dict
                else:
                    # Standard Text Content (Description, Origin, etc.)
                    # We use 'inner_text' to get clean visible text
                    content_text = panel.inner_text().replace("\n", " ").strip()
                    product_data[section_title] = content_text
                    
            except Exception as e:
                print(f"Skipping a section due to error: {e}")

        # --- OUTPUT RESULTS ---
        print("\n" + "="*40)
        for key, value in product_data.items():
            print(f"[{key}]:")
            print(f"   {value}")
            print("-" * 20)
        print("="*40)

if __name__ == "__main__":
    # Example URL (ensure this URL matches the product type you want)
    url = "https://nakup.itesco.cz/groceries/cs-CZ/products/212302210" 
    scrape_product_details(url)