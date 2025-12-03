import requests
from time import sleep
import json


categories = {
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

cookies = {
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
    'ak_bmsc': '1AC8AE9978E06D7FB6469C1E238159C0~000000000000000000000000000000~YAAQFpJkX9RCrCWaAQAAxoLLLx1oR4deG/W8pqoStuRZH18Z3/H5xv3oMxL6CCwt+0qo4kWZ3c55B6DLxQlJFGpUxfyT7F0ZocDNI5PvdvUUqaHwilQy09VQvUE7NZUWob5fxAwBAxSFLSnaM4E9bSHWpD7zZih4mwJX0T4K5LcdtTghWYt08VtmIw1IJXrviRxJCUDp2jBnfK46hRepyeQT/rQaxxJR4hqFZDkpiZtoiodj0L6jBsDWuXA6mjnjXgBhN2Ag+Al4O8R80tIIqN3lv9Q0gfa7t5fUrKxPbEln1361KYkP0AS7Hl8D37XnJ9VwQ5heaARVO8igXRrjI35lwRFVLqg9COnaaR/9OVxCkmpZIjykarRvxpeVW2Ghf9CbfP+1kVR9nAgGqqQiOVt4Sh+WvtAc0T14O/wx8egeH6MogP01VX/EnyauqiY7fgs=',
    'AWSALB': '0ngSaaiJQdn/KXax2Gty+vhMRlbFVipkLOgijIZuZFkwS0fjRB0WVSnyeZI9KX2zlGtrOMlgxcATPI9j0wDrsdArg5gImEB94jToW9SvWW73yWd1DjFeVM7tuadK',
    'AWSALBCORS': '0ngSaaiJQdn/KXax2Gty+vhMRlbFVipkLOgijIZuZFkwS0fjRB0WVSnyeZI9KX2zlGtrOMlgxcATPI9j0wDrsdArg5gImEB94jToW9SvWW73yWd1DjFeVM7tuadK',
    'bm_sv': '3A07B2A6AB20AA8528B57C4298AD5E79~YAAQh27UF/YJjhCaAQAAyZD7Lx0csjlQaMlrqySYnKomb7OAPcAAiwPFl+tby9Mn+lZt3DmXKdYcvuHwXU1ncXpTa3gQRfzWeTp3/tNF1RKMtt77kgohjsD5FyAuCA5TXkdXOfD9RAPe73j87mzNcor4twD0Gifz1+YWvPwqeY+iz7coeMlvicbpC+HNJmA//Nv+zIEUw28cXGEIFtNbVEtKRBhu6Q3gtBMOX8KgF4mYw5VMCyQ8Y8Hza0pZ+Ext~1',
    'bm_sz': '653B7D33768B9588A468F2288793A307~YAAQh27UF/cJjhCaAQAAyZD7Lx13anJ6JYCwnDI//040dhF/H/FqoT0sdc7xv88HlK9Wwdl9/hAT0vNj5HX8HEuGk5ZLl4mbY4eij0SDlDlPbBuDfwJplEcUhU+tgi4Jcw3g/YXXUkEK8jwYleufOE1jDXRaveVoBpES3RQFmryiHlZGLKeVl9T36t/yKr2y6+ZtGC3Zo5uDyL2tpSldOCdjqEizNIFFAMuyKSQMeIyTvbrwqA3AE0gUmeVOjmMkxe6Woo2aLZhYuMD9T5iQrqMYvEI1tX3z+NHLeBDO34aajmdeyRJ/auQPnTnUnvaRO0JRfYyrWBRRhAuijzwn8BHN5V8GfR9OYJgRUkXZ0sVTlDI6WxPuCq/LTy1mWbP/ND4SvVjcok09E7M9syJDi01TwiYhRmMAO5U8qc+QAkDCsoxeNvV7ODP0LNmY4X9I~3355970~4473140',
}

headers = {
    'accept': '*/*',
    'accept-language': 'cs-CZ,cs;q=0.9',
    'apollographql-client-name': 'cz-alb-web-stores',
    'apollographql-client-version': '9f7f73067ae74ca1179954e9a94f3a23f1822b6b',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.albert.cz/shop/Ovoce-a-zelenina/c/zeG001?intcmp=web_all_megamenu_ovoce-zelenina_still_hp_cz&q=:relevance&sort=relevance&',
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
    # 'cookie': 'VersionedCookieConsent=v:2,essential:1,analytics:0,social:0,perso_cont_ads:0,ads_external:0; _abck=D1FFD147D3F06FC3D89A22F7CA4343B0~-1~YAAQFpJkX+hBrCWaAQAAIX3LLw4pb222HUiveb2uWWPrFAJXI8CsDbMGR6dkB5sc55QYw2EysQKBYWCPO22ZIvmD5mECtVo0xFIUJsrnQa/xE9UshEjE282BmNdolUFJzA/O4jONbVFTVhTIxw0ej7YNM5OJaZNqglPPK8OQDeXKkhkdngctFtIrjYnRBr9PMb0aE7SpMuGEmdYwlCSBUcLnv9Eudr9/G176KbS3GH/AAaUBOwBBjj98p+xLWLVy8C4qnVQJyPUfHdjX52Y4a0ndc3CH0Y9VDNxE4UQK11wLdoGX8uWxv57fTFEzx2vN6ee4uawxaFzg9igmhDQB5Z6r0KV3xclUmDnaysxPWADnD8tSJFmUcq1er0bM5aU+S22EPNWwCahPiCuMof58PvQGY/TCjLCt/rhJhbIChM1E49tEos44iD1JGKwQeMnyxfSK+YPupkRy5AWVV5ptcBB4ITYUZB00tBpzj6HNfNY=~-1~-1~-1~-1~-1; rxVisitor=1761738456259O5KLM8E2EE88IC9FMACS0I29C3N2H5TD; dtPC=-13787$138456258_279h1vAHLIGGIFRQRLKRHKMUEURDCRBEHCILAQ-0e0; dtSa=-; customer-ecom-state=NOT_DEFINED; groceryCookieLang=cs; liquidFeeThreshold=0; deviceSessionId=f121eb9d-8bfe-41f0-80c9-f0a8cbd416a0; dtCookie=v_4_srv_11_sn_5MC5M2BHNMVR4CN7UDL99DNP37AI7A9L_perc_100000_ol_0_mul_1_app-3Ac32cb5e5575cf68e_0; rxvt=1761740257377|1761738456260; ak_bmsc=1AC8AE9978E06D7FB6469C1E238159C0~000000000000000000000000000000~YAAQFpJkX9RCrCWaAQAAxoLLLx1oR4deG/W8pqoStuRZH18Z3/H5xv3oMxL6CCwt+0qo4kWZ3c55B6DLxQlJFGpUxfyT7F0ZocDNI5PvdvUUqaHwilQy09VQvUE7NZUWob5fxAwBAxSFLSnaM4E9bSHWpD7zZih4mwJX0T4K5LcdtTghWYt08VtmIw1IJXrviRxJCUDp2jBnfK46hRepyeQT/rQaxxJR4hqFZDkpiZtoiodj0L6jBsDWuXA6mjnjXgBhN2Ag+Al4O8R80tIIqN3lv9Q0gfa7t5fUrKxPbEln1361KYkP0AS7Hl8D37XnJ9VwQ5heaARVO8igXRrjI35lwRFVLqg9COnaaR/9OVxCkmpZIjykarRvxpeVW2Ghf9CbfP+1kVR9nAgGqqQiOVt4Sh+WvtAc0T14O/wx8egeH6MogP01VX/EnyauqiY7fgs=; AWSALB=0ngSaaiJQdn/KXax2Gty+vhMRlbFVipkLOgijIZuZFkwS0fjRB0WVSnyeZI9KX2zlGtrOMlgxcATPI9j0wDrsdArg5gImEB94jToW9SvWW73yWd1DjFeVM7tuadK; AWSALBCORS=0ngSaaiJQdn/KXax2Gty+vhMRlbFVipkLOgijIZuZFkwS0fjRB0WVSnyeZI9KX2zlGtrOMlgxcATPI9j0wDrsdArg5gImEB94jToW9SvWW73yWd1DjFeVM7tuadK; bm_sv=3A07B2A6AB20AA8528B57C4298AD5E79~YAAQh27UF/YJjhCaAQAAyZD7Lx0csjlQaMlrqySYnKomb7OAPcAAiwPFl+tby9Mn+lZt3DmXKdYcvuHwXU1ncXpTa3gQRfzWeTp3/tNF1RKMtt77kgohjsD5FyAuCA5TXkdXOfD9RAPe73j87mzNcor4twD0Gifz1+YWvPwqeY+iz7coeMlvicbpC+HNJmA//Nv+zIEUw28cXGEIFtNbVEtKRBhu6Q3gtBMOX8KgF4mYw5VMCyQ8Y8Hza0pZ+Ext~1; bm_sz=653B7D33768B9588A468F2288793A307~YAAQh27UF/cJjhCaAQAAyZD7Lx13anJ6JYCwnDI//040dhF/H/FqoT0sdc7xv88HlK9Wwdl9/hAT0vNj5HX8HEuGk5ZLl4mbY4eij0SDlDlPbBuDfwJplEcUhU+tgi4Jcw3g/YXXUkEK8jwYleufOE1jDXRaveVoBpES3RQFmryiHlZGLKeVl9T36t/yKr2y6+ZtGC3Zo5uDyL2tpSldOCdjqEizNIFFAMuyKSQMeIyTvbrwqA3AE0gUmeVOjmMkxe6Woo2aLZhYuMD9T5iQrqMYvEI1tX3z+NHLeBDO34aajmdeyRJ/auQPnTnUnvaRO0JRfYyrWBRRhAuijzwn8BHN5V8GfR9OYJgRUkXZ0sVTlDI6WxPuCq/LTy1mWbP/ND4SvVjcok09E7M9syJDi01TwiYhRmMAO5U8qc+QAkDCsoxeNvV7ODP0LNmY4X9I~3355970~4473140',
}


def clean_albert_data(json_data):
    products_data = []

    # Safely navigate to the 'products' list
    try:
        products = json_data['data']['categoryProductSearch']['products']
    except (TypeError, KeyError):
        return products_data # Return empty list if structure is unexpected

    for product in products:
        category = product.get('firstLevelCategory', {}).get('name', '')
        name = product.get('name')
        price_info = product.get('price', {})
        images = product.get('images', [])
        print(f"Processing product: {name}")

        # 1. Extract Image URL (prefer 'xlarge' and 'PRIMARY', otherwise the first image)
        image_url = None
        if images:
            # Look for "xlarge" and "PRIMARY"
            for image in images:
                if image.get('format') == 'xlarge' and image.get('imageType') == 'PRIMARY':
                    image_url = image.get('url')
                    break

            # If not found, fall back to the URL of the first image
            if not image_url:
                image_url = images[0].get('url')

            # Ensure the image URL is absolute. If it's relative, prefix the site's base URL.
            if image_url and not image_url.startswith(('http://', 'https://')):
                image_url = 'https://www.albert.cz/' + image_url.lstrip('/')

        # 2. Extract Price details
        # 'formattedValue' is often the original/strikethrough price
        formatted_value = price_info.get('formattedValue')
        # 'discountedPriceFormatted' is the current/sale price
        current_price = price_info.get('discountedPriceFormatted') 

        # NOTE: formatted_value and current_price can be equal if the item isnt on sale

        unit_code = price_info.get('unitCode')
        # "supplementaryPriceLabel1": "1 kg = 199,60 Kč", so this is kinda neccessary. sorry
        unit_price_formatted = float(price_info.get('supplementaryPriceLabel1', '0').split('=')[1].split('Kč')[0].replace('.', '').replace(',', '.').replace(" ", "").strip()) if price_info.get('supplementaryPriceLabel1') else None

        # 3. Extract product URL (may be relative)
        product_url = product.get('url')
        if product_url and not product_url.startswith(('http://', 'https://')):
            product_url = 'https://www.albert.cz/' + product_url.lstrip('/')

        products_data.append({
            'source': 'albert',
            'product_category': category,
            'item_name': name,
            'image_url': image_url, # float("43,84 Kč".split(" ")[0].replace(",", "."))
            'original_price': float(formatted_value.split(" ")[0].replace(".", "").replace(",", ".")), #  "286,40 Kč"
            'sale_price': float(current_price.split(" ")[0].replace(".", "").replace(",", ".")), # "143,84 Kč"
            'sale_ppu': unit_price_formatted,  # eg "89.9", we need to add the unit from the unit_code
            'unit_code': unit_code, # eg kg, g, l etc.
            'product_url': product_url,
            'sale_requirement': None  # Indicate what the sale price requires
        })

    return products_data

def is_product_response_empty(response: dict) -> bool:
    """
    Checks if the JSON response is the one without any products.
    """
    try:
        products_list = response['data']['categoryProductSearch']['products']

        if not products_list:
            return True
        else:
            return False

    except KeyError:
        print("Warning: JSON structure is missing expected keys.")
        return False # Or True, depending on how you want to handle errors


if __name__ == "__main__":
    all_products = []

    params = {
        'operationName': 'GetCategoryProductSearch',
        'variables': '{"lang":"cs","searchQuery":":relevance","sort":"relevance","category":"CATEGORY_CODE","pageNumber":PAGE_NUMBER,"pageSize":PAGE_SIZE,"filterFlag":true,"fields":"PRODUCT_TILE","plainChildCategories":true}',
        'extensions': '{"persistedQuery":{"version":1,"sha256Hash":"afce78bc1a2f0fe85f8592403dd44fae5dd8dce455b6eeeb1fd6857cc61b00a2"}}',
    }
    page_size = 50 # Max number of products albert allows us to request
    for code, name in categories.items():
        for page_index in range(0, 500):  # Arbitrarily large number, since we stop when no products are returned
            print(f"Fetching data for category: {code} ({name}), page: {page_index}. ")
            
            # Copy params and replace the hard-coded category value inside the JSON string
            this_params = params.copy()
            # params['variables'] contains a JSON string with the category; replace the value safely
            this_params['variables'] = this_params['variables'].replace('CATEGORY_CODE', code)
            this_params['variables'] = this_params['variables'].replace('PAGE_NUMBER', str(page_index))
            this_params['variables'] = this_params['variables'].replace('PAGE_SIZE', str(50))
            
            response = requests.get('https://www.albert.cz/api/v1/', params=this_params, cookies=cookies, headers=headers)
            if is_product_response_empty(response.json()):
                print(f"No more products found for category {code} on page {page_index}. Stopping.")
                break

            try:
                albert_data = response.json()
                print(f"Length of items on current page: {len(albert_data.get('data', {}).get('categoryProductSearch', {}).get('products', []))}")
                all_products.extend(clean_albert_data(albert_data))
            except Exception as e:
                print(f"Failed to parse JSON for category {code}: {e}")
                continue
            sleep(0.1)  # Be polite and avoid hitting the server too quickly


    for product in all_products:
        print(product)
    
    print("====================================")
    print(all_products)

    # Save collected products to a JSON file
    with open('albert_products.json', 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)