from base_scraper import BaseScraper
from typing import List, Dict, Any
from loguru import logger
from models.models import Product


class BillaScraper(BaseScraper):
    def __init__(self):
        super().__init__("billa")
        categories_list = [
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
        self.categories = {c: c for c in categories_list}
        
        self.session.cookies.update({
            'XSRF-TOKEN': '9438d651-5e76-45b3-ae10-f3531882e07e',
            'OptanonAlertBoxClosed': '2025-12-03T10:14:03.198Z',
            'jts-rw': '{"u":"1291176475684166985018"}',
            'jctr_sid': '18596176544678364134515',
            '_clck': '1w71g7t%5E2%5Eg1r%5E0%5E2163',
            '_uetsid': '4a75b700d67711f0857edbd92a190a95',
            '_uetvid': 'cff49a00d03011f087907952d7f53f2e',
            'OptanonConsent': 'isGpcEnabled=0&datestamp=Thu+Dec+11+2025+10%3A57%3A37+GMT%2B0100+(Central+European+Standard+Time)&version=202510.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&genVendors=&consentId=bed1a886-4afa-4f63-8413-d365969d56a9&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A0%2CC0004%3A0&intType=2&geolocation=%3B&AwaitingReconsent=false',
            '_clsk': '1641g7l%5E1765447903945%5E5%5E1%5Ey.clarity.ms%2Fcollect',
        })
        
        self.session.headers.update({
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'credentials': 'include',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'x-request-id': '516d1d45-f11d-4db1-9364-5d2fc43a5c56-1765446810341',
            'x-xsrf-token': '9438d651-5e76-45b3-ae10-f3531882e07e',
        })

    def fetch_category(self, category_code: str, page: int) -> Dict[str, Any]:
        """Fetch products from Billa API for a given category and page."""
        params = {
            'page': str(page),
            'sortBy': 'relevance',
            'enableStatistics': 'false',
            'enablePersonalization': 'false',
            'pageSize': '500',
        }
        
        try:
            response = self.session.get(
                f'https://shop.billa.cz/api/product-discovery/categories/{category_code}/products',
                params=params,
                timeout=15,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Request failed for category {category_code} page {page}: {e}")
            return {}

    def parse_response(self, response_data: Dict[str, Any], category_name: str) -> List[Product]:
        """Transform Billa JSON data into Product objects."""
        products = []
        results = response_data.get("results", [])
        
        logger.info(f"Processing {len(results)} products from category {category_name}")
        
        for product in results:
            try:
                # Basic product info
                item_name = product.get("name")
                product_slug = product.get("slug")
                
                # Category
                parent_categories = product.get("parentCategories", [[]])
                product_category = parent_categories[0][0].get("name", "Unknown Category") if parent_categories and parent_categories[0] else category_name
                
                # Image
                images = product.get("images", [])
                image_url = images[0] if images else None
                
                # Pricing
                price_data = product.get("price", {})
                regular_price_data = price_data.get("regular", {})
                loyalty_price_data = price_data.get("loyalty", {})
                
                # Original Price (convert from cents)
                original_price_cents = regular_price_data.get("value")
                if original_price_cents is None:
                    continue  # Skip products without price
                original_price = original_price_cents / 100
                
                # Sale Price and Requirements
                sale_price = original_price
                sale_ppu = None
                sale_requirement = None
                
                if loyalty_price_data:
                    sale_price_cents = loyalty_price_data.get("value")
                    if sale_price_cents is not None:
                        sale_price = sale_price_cents / 100
                        sale_requirement = "billa_card"
                
                # Price per unit
                ppu_cents = loyalty_price_data.get("perStandardizedQuantity") or regular_price_data.get("perStandardizedQuantity")
                if ppu_cents is not None:
                    sale_ppu = ppu_cents / 100
                
                # Unit code
                unit_code = price_data.get("baseUnitLong", "").lower() or None
                
                # Product URL
                product_url = f"https://shop.billa.cz/produkt/{product_slug}"
                
                # Create Product object
                product_obj = Product(
                    source="billa",
                    product_category=product_category,
                    item_name=item_name,
                    image_url=image_url,
                    original_price=original_price,
                    sale_price=sale_price,
                    sale_ppu=sale_ppu,
                    unit_code=unit_code,
                    product_url=product_url,
                    sale_requirement=sale_requirement
                )
                
                products.append(product_obj)
                
            except Exception as e:
                logger.warning(f"Failed to parse product: {e}")
                continue
        
        return products




if __name__ == "__main__":
    scraper = BillaScraper()
    scraper.run()
    scraper.save_to_json('output/billa_products.json')