from base_scraper import BaseScraper
from typing import List, Dict, Any
from loguru import logger
from models.models import Product
from utils.price_utils import parse_price_string


class AlbertScraper(BaseScraper):
    def __init__(self):
        super().__init__("albert")
        self.categories = {
            'zeG001': 'Ovoce a zelenina',
            'zeJ001': 'Mléčné a chlazené',
            'zeF001': 'Pečivo a cukrárna',
            'zeL001': 'Trvanlivé',
            'zeM001': 'Nápoje',
            'zeH001': 'Maso a ryby',
            'zeK001': 'Uzeniny a lahůdky',
            'zeJ005': 'Mražené',
            'zeN001': 'Speciální výživa',
        }
        
        self.session.cookies.update({
            'VersionedCookieConsent': 'v:2,essential:1,analytics:0,social:0,perso_cont_ads:0,ads_external:0',
            '_abck': 'D1FFD147D3F06FC3D89A22F7CA4343B0~-1~YAAQFpJkX+hBrCWaAQAAIX3LLw4pb222HUiveb2uWWPrFAJXI8CsDbMGR6dkB5sc55QYw2EysQKBYWCPO22ZIvmD5mECtVo0xFIUJsrnQa/xE9UshEjE282BmNdolUFJzA/O4jONbVFTVhTIxw0ej7YNM5OJaZNqglPPK8OQDeXKkhkdngctFtIrjYnRBr9PMb0aE7SpMuGEmdYwlCSBUcLnv9Eudr9/G176KbS3GH/AAaUBOwBBjj98p+xLWLVy8C4qnVQJyPUfHdjX52Y4a0ndc3CH0Y9VDNxE4UQK11wLdoGX8uWxv57fTFEzx2vN6ee4uawxaFzg9igmhDQB5Z6r0KV3xclUmDnaysxPWADnD8tSJFmUcq1er0bM5aU+S22EPNWwCahPiCuMof58PvQGY/TCjLCt/rhJhbIChM1E49tEos44iD1JGKwQeMnyxfSK+YPupkRy5AWVV5ptcBB4ITYUZB00tBpzj6HNfNY=~-1~-1~-1~-1~-1',
            'rxVisitor': '1761738456259O5KLM8E2EE88IC9FMACS0I29C3N2H5TD',
            'dtPC': '-13787$138456258_279h1vAHLIGGIFRQRLKRHKMUEURDCRBEHCILAQ-0e0',
            'dtSa': '-',
            'customer-ecom-state': 'NOT_DEFINED',
            'groceryCookieLang': 'cs',
            'liquidFeeThreshold': '0',
            'deviceSessionId': 'f121eb9d-8bfe-41f0-80c9-f0a8cbd416a0',
            'dtCookie': 'v_4_srv_11_sn_5MC5M2BHNMVR4CN7UDL99DNP37AI7A9L_perc_100000_ol_0_mul_1_app-3Ac32cb5e5575cf68e_0',
            'rxvt': '1761740257377|1761738456260',
        })
        
        self.session.headers.update({
            'accept': '*/*',
            'accept-language': 'cs-CZ,cs;q=0.9',
            'apollographql-client-name': 'cz-alb-web-stores',
            'apollographql-client-version': '9f7f73067ae74ca1179954e9a94f3a23f1822b6b',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Brave";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'x-apollo-operation-id': 'e2e886640745ecc178a7063af2924a312585e81bbf6a7f7c70a38e8389bd9e31',
            'x-apollo-operation-name': 'GetCategoryProductSearch',
            'x-default-gql-refresh-token-disabled': 'true',
        })

    def fetch_category(self, category_code: str, page: int) -> Dict[str, Any]:
        """Fetch products from Albert GraphQL API for a given category and page."""
        params = {
            'operationName': 'GetCategoryProductSearch',
            'variables': f'{{"lang":"cs","searchQuery":":relevance","sort":"relevance","category":"{category_code}","pageNumber":{page},"pageSize":50,"filterFlag":true,"fields":"PRODUCT_TILE","plainChildCategories":true}}',
            'extensions': '{"persistedQuery":{"version":1,"sha256Hash":"afce78bc1a2f0fe85f8592403dd44fae5dd8dce455b6eeeb1fd6857cc61b00a2"}}',
        }

        return self.request_json(
            method="get",
            url='https://www.albert.cz/api/v1/',
            error_message=f"Request failed for category {category_code} page {page}",
            params=params,
            timeout=15,
        )

    def parse_response(self, response_data: Dict[str, Any], category_name: str) -> List[Product]:
        """Transform Albert JSON data into Product objects."""
        products = []
        
        try:
            product_list = response_data['data']['categoryProductSearch']['products']
        except (TypeError, KeyError):
            logger.warning(f"Unexpected response structure for category {category_name}")
            return products

        logger.info(f"Processing {len(product_list)} products from category {category_name}")

        for product in product_list:
            try:
                # Basic info
                category = product.get('firstLevelCategory', {}).get('name', category_name)
                name = product.get('name')
                if not name:
                    continue
                
                price_info = product.get('price', {})
                images = product.get('images', [])
                
                # Extract Image URL (prefer 'xlarge' and 'PRIMARY')
                image_url = None
                if images:
                    for image in images:
                        if image.get('format') == 'xlarge' and image.get('imageType') == 'PRIMARY':
                            image_url = image.get('url')
                            break
                    
                    if not image_url and images:
                        image_url = images[0].get('url')
                    
                    # Ensure absolute URL
                    if image_url and not image_url.startswith(('http://', 'https://')):
                        image_url = 'https://www.albert.cz/' + image_url.lstrip('/')
                
                # Extract pricing
                formatted_value = price_info.get('formattedValue')  # Original price
                current_price = price_info.get('discountedPriceFormatted')  # Sale price
                
                if not formatted_value or not current_price:
                    continue
                
                # Parse prices (remove currency and convert commas to dots)
                original_price = parse_price_string(formatted_value)
                sale_price = parse_price_string(current_price)
                
                if original_price is None or sale_price is None:
                    continue
                
                unit_code = price_info.get('unitCode')
                
                # Parse unit price
                unit_price_formatted = None
                if price_info.get('supplementaryPriceLabel1'):
                    try:
                        # Example: "1 ks = 12,90 Kč"
                        label_parts = price_info.get('supplementaryPriceLabel1', '').split('=')
                        if len(label_parts) > 1:
                            unit_price_formatted = parse_price_string(label_parts[1])
                    except (IndexError, ValueError):
                        pass
                
                # Extract product URL
                product_url = product.get('url')
                if product_url and not product_url.startswith(('http://', 'https://')):
                    product_url = 'https://www.albert.cz/' + product_url.lstrip('/')
                
                if not product_url:
                    continue
                
                # Create Product object
                product_obj = Product(
                    source="albert",
                    product_category=category,
                    item_name=name,
                    image_url=image_url,
                    original_price=original_price,
                    sale_price=sale_price,
                    sale_ppu=unit_price_formatted,
                    unit_code=unit_code,
                    product_url=product_url,
                    sale_requirement=None
                )
                
                products.append(product_obj)
                
            except Exception as e:
                logger.warning(f"Failed to parse product: {e}")
                continue
        
        return products




if __name__ == "__main__":
    scraper = AlbertScraper()
    scraper.run_and_save('output/albert_products.json')