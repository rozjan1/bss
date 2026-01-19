import json
import re
import requests
from typing import Dict, Any
from loguru import logger
from pathlib import Path
from base_enricher import BaseProductEnricher
from bs4 import BeautifulSoup

def extract_product_info(html_content: str, product_id: str) -> dict:
    """
    Dynamically extracts ingredients, allergens, and description for a product
    from embedded JSON data OR directly from HTML structure (fallback).

    Args:
        html_content: A string containing the entire HTML document.
        product_id: The ID of the product (e.g., '212302210') to look up.

    Returns:
        A dictionary containing the extracted product information.
    """
    results = {
        "ingredients": None,
        "allergens": None,
        "description": None
    }

    # --- STRATEGY 1: Parse from HTML DOM (More robust for SSR/Client-rendered HTML) ---
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Helper to find accordion sections by header text
        def get_section_text(header_keyword):
            # Find all accordion headers
            headers = soup.find_all(attrs={"data-testid": "accordion-control"})
            for header in headers:
                if header_keyword.lower() in header.get_text().strip().lower():
                    # Find the associated panel
                    #The panel ID is usually in aria-controls of the button
                    panel_id = header.get('aria-controls')
                    if panel_id:
                        panel = soup.find(id=panel_id)
                        if panel:
                            return panel
            return None

        # 1. Description
        # Look for "Popis produktu"
        desc_panel = get_section_text("Popis produktu")
        if desc_panel:
            # Usually under a header "Popis" inside the panel
            # or just take all text in the panel
            description_container = desc_panel.find(class_="OobGYfu9hvCUvH6") # Fallback to class seen in HTML
            if not description_container:
                 # Try finding the 'Popis' sub-header and taking next sibling
                 sub_headers = desc_panel.find_all("h3")
                 for sub in sub_headers:
                     if "Popis" in sub.get_text():
                         description_container = sub.find_next_sibling("div")
                         break
            
            if description_container:
                results['description'] = description_container.get_text(strip=True)
            else:
                 # Fallback: just get all text from panel
                 results['description'] = desc_panel.get_text(" ", strip=True)

        # 2. Ingredients & Allergens (Usually in "Složení")
        ing_panel = get_section_text("Složení")
        if ing_panel:
            # Ingredients
            # Look for sub-header "Ingredience"
            ing_header = ing_panel.find('h3', string=lambda t: t and "Ingredience" in t)
            if ing_header:
                ing_div = ing_header.find_next_sibling('div')
                if ing_div:
                    # Clean text (remove 'strong' tags if needed, but get_text does that)
                    results['ingredients'] = [ing_div.get_text(strip=True)]
            
            # Allergens
            # Look for sub-header "Informace o alergenech"
            allergen_header = ing_panel.find('h3', string=lambda t: t and "Informace o alergenech" in t)
            if allergen_header:
                allergen_div = allergen_header.find_next_sibling('div')
                if allergen_div:
                    val = allergen_div.get_text(strip=True).replace("Obsahuj: ", "").replace("Obsahuje:", "").strip()
                    results['allergens'] = [val]

        # If we found data, return it. If not, try the JSON fallback.
        if any(results.values()):
            return results

    except Exception as e:
        # Log error but continue to JSON strategy
        pass
        # logger.warning(f"DOM parsing failed: {e}")

    # --- STRATEGY 2: Find and extract the JSON data containing the product info (Legacy/Backup) ---
    
    json_regexes = [
        # 1. Matches the correct tag type from your HTML output
        r'<script[^>]*type="asparagus-data"[^>]*>\s*(\{[\s\S]*?\})\s*<\/script>',
        # 2. A fallback to the common Apollo cache naming convention
        r'<script[^>]*type="application/discover\+json"[^>]*>\s*(\{[\s\S]*?\})\s*<\/script>',
    ]
    
    json_data_str = None
    for regex in json_regexes:
        match = re.search(regex, html_content)
        if match:
            json_data_str = match.group(1).strip()
            break
            
    if not json_data_str:
        return {"error": "Could not find a relevant embedded JSON script tag."}

    try:
        data = json.loads(json_data_str)
    except json.JSONDecodeError as e:
        return {"error": f"Failed to decode JSON from script tag: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred during JSON extraction: {e}"}

    # --- 2. Dynamically Locate the Product Data within the Apollo Cache ---
    
    try:
        # Navigate to the Apollo Cache root (consistent path)
        apollo_cache = data.get('mfe-orchestrator', {}).get('props', {}).get('apolloCache', {})
        
        # Search through all keys in the cache for one starting with 'ProductType:' 
        # and containing the target product_id.
        product_ref_key = None
        target_prefix = "ProductType:"
        
        for key in apollo_cache:
            if key.startswith(target_prefix) and product_id in key:
                product_ref_key = key
                break
                
        if not product_ref_key:
            return {"error": f"Product data with ID '{product_id}' not found dynamically in apolloCache."}
        
        product_data = apollo_cache[product_ref_key]

        # --- 3. Extract the required fields (Cleaned/Corrected Logic) ---

        # Extracting ingredients (cleaning up HTML strong tags)
        raw_ingredients = product_data.get('details', {}).get('ingredients')
        if raw_ingredients:
            # Clean up the HTML strong tags using regex
            cleaned_ingredients = [
                re.sub(r'<strong\b[^>]*>|<\/strong>', '', item).strip()
                for item in raw_ingredients
            ]
            results['ingredients'] = cleaned_ingredients

        # Extracting allergens (Corrected: extracting the allergen name from the list of objects)
        raw_allergens = product_data.get('details', {}).get('allergens')
        if raw_allergens:
             # Assumes the allergen name is the first value in the 'values' list
             results['allergens'] = [item['values'][0] for item in raw_allergens if item.get('values')]
        
        # Extracting description
        description_list = product_data.get('description')
        if description_list and isinstance(description_list, list):
            results['description'] = description_list[0]
            
    except KeyError as e:
        results["error"] = f"Missing expected key in JSON structure: {e}"
        return results
    except Exception as e:
        results["error"] = f"An unexpected error occurred during data processing: {e}"
        return results
        
    return results

# --- Session Management and Execution ---

PRODUCT_ID = '212302210'

# 1. Define the cookie dictionary (as provided by the user)
cookies_dict = {
    '_ait': '9fba039e-2e1e-ac5f-ed5d-289f9f45cf05',
    'aitHealthCheckDone': '1',
    'atrc': '58493dbf-253c-4ca6-92d2-2dfed0d5ee1c',
    'OptanonAlertBoxClosed': '2025-11-26T21:05:49.822Z',
    'eupubconsent-v2': 'CQbfhFgQbfhFgAcABBCSCGFwAPLAAELAAAYgF5wAQF5gXnABAXmAAAAA.flgACFgAAAAA',
    'cookiePreferences': '%7B%22experience%22%3Atrue%2C%22advertising%22%3Atrue%7D',
    '_ga': 'GA1.1.1747282449.1764191747',
    '_gcl_au': '1.1.484248307.1764191747',
    'FPAU': '1.1.484248307.1764191747',
    '_csrf': 'S-7vQNFmU9ykC9m2d7saPOCC',
    'uws_storage': '%22cookie%22',
    'AMCVS_E4860C0F53CE56C40A490D45%40AdobeOrg': '1',
    's_cc': 'true',
    'bm_mi': 'C9E3501F04F5A48880137205DE8A0B37~YAAQXklnaNSnBqeaAQAA1t4VBx7W/QTYr224W+cgR7cJDooOePVBPtCKOjYb5k8eRxq7CUmZxR14YJcwwM7UyUzhXC7jeLy1a4bbpghpcXWjH1S5N1Z365rBz2vllrQFEeCFuJwc+4aR0IbefGmKjsKaYbmn76nV7hMipLl+5itVY5t3WG3YV9T06WCm8krVoLwX67lMsod+sJ26uCg+5yWZqpqO3mWtGCimViLCaMdLRLe41ulbUWA9dKxvMat/1vCqWvGbb7kwpHvTOANAKGyw6qTNSPTceLQzRrqAsWve5Yp4YIercuw2vdfmS5OfCjwhWOEFxVZR8innpSfpQBC6HBW18tLXcP+akIP2GA==~1',
    'ak_bmsc': '7F70708A588262E935A8F52640E7E946~000000000000000000000000000000~YAAQXklnaOSnBqeaAQAAOeIVBx5HumnUKOeITqe1RBFrlpmv2+9tWfJPmO/W+6puPkf2bFPu0shHetcDhcGhblSdfxh+dblqsDC3weIcwH9RWbhiWmbBxMxQXHmM634cn5FZ5+BaikWGgiV8u6p6OhMvgeG+L3b2RhFCiGgQLRrnoOwp8bAMoxM9/N0F5mJd8r5cI1WllFluqhyiekUCJg9zZSlhzldXSNhmezhHUCF7Y7bZrhoUFy4HCsit2jPBikdMg46GQXRAINotCk+AcYgqNob3D5muELo5IIye4sYr45cO8J1THJ10jECpvV6yRxgZqeiwmxoG8YDgnrpdntJ/dKDAbfPGycxzGvfma8619iqxu/1VYahjBtIvlW5SJHs4DoR77+VYH748hOnZcnQBeUfvJMfAkaYpWdzq00e3s17R0cjrTGrcsRX3mSNLhZWV3VsVm2Rdrpz+N2vDpVsPrma0PArflEQtjgoJW4HNR/WQF/iNZ4wbKVh5baO9z1nF2gAYyOQKI59eWJlBfQqO9A==',
    'uws_rate_comparators': '%7B%22global%22%3A76701709%7D%7Csession_timeout',
    'AMCV_E4860C0F53CE56C40A490D45%40AdobeOrg': '179643557%7CMCIDTS%7C20432%7CMCMID%7C39323309555778142183195783528547581714%7CMCAAMLH-1765955233%7C6%7CMCAAMB-1765955233%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1765357633s%7CNONE%7CMCAID%7CNONE%7CMCSYNCSOP%7C411-20426%7CvVersion%7C5.5.0',
    's_gpv_pn': 'pdp_byst%C5%99ick!x1.pomaz!x1nka.200g',
    'timestamp': '1765355042158',
    'bm_ss': 'ab8e18ef4e',
    'bm_s': 'YAAQCE4SAkqrQ7WaAQAATjZcBwQKERl/gXAcaVN7WNC04PQEt72Y5BrqojBhCX4qooXmuuWBho1+FerrDOmoEkD4oANqLAoH9Bx2e0exSSRSyAfswOh6lkn/a6g8EbO9MfQCP1JlkPBl6uksJHCRj+v7pQFu2yh8mfn6TnXJJuHyhpLgS6NHojFTgrEtgUiVULQwW9iwY/uzL0UH224akqOccboVJtzPTMRMjfQZEiNaiO6zp1XbXYzkIgoWhmrMTLpewvV4kRfvigpPoMImbV1u40fomWWAcWHRJhGh8fO3nsGHzJBNddFBkd5ZRTi8IAHWviyxJSPFvQ7yyEPkzLrwHsGUc3qZwu1/DBh+BzfYCn97UKOMTtg0S11K+eV9BWSVF5+TBM3SIrOy8Y7EPraAt62jiYODM0xCyorliTL3aNMW8M05w07eGu8kXz792pq8nERS3LMeEfA44l25wE2QizjVzkGKSSRDVjXPEWjrX7AuaUj7cYasUY+jSvu5hcnYJC3HlApCWZQaolvnOnMxP6bYEryM1zTgT8qx/4hlCQHL0f21VAZWoDMhS9ofjQoGZqp36A==',
    'bm_so': '41412D23DE19C64D856775FDE60F5BD1539CDF7A8658AFFC80E33D100362BFCF~YAAQCE4SAkurQ7WaAQAATjZcBwXokhlp/9AOPgijiBBkVDm0hQpVOlQZ+3D7Q4eis0JQhmhf3dFdYu2ewVY9kS/UnPijgLTpO2BAERFTsiLTbHGTxKBv2elytssNQis/200BjYvVpXY3leI4oobEmfwl33EJgCrry9Etp6YxsgnpqPKcdVd9QaFeHD6yA9b2RA5U5D4qTIuTDzWW+D9PIlxa1g6bPWoinkuGjygR2j4IosloOT0aL1VMv64LFcVWohL+zpIju+tNJ8xtSwcTP1evmWQuF/1pIdWLs/0werJG3y8R7+FBntIkKncXND0TvobysMHJ5JI+rgQ1RR+rJ9biX+Lr/18S9vkHy18zURFub9QAzZ50K+WkBPW1/U7JI+t6WjUHZqLzB7CxOd+K/nFtfwjHu8Vp2IFgfvix5dW+KqOjqp5dmXPSShlGUJIop4YXd4wdT98MhWwEEk5X',
    'bm_sz': '16738036308DF30D6E82935A3409ADE8~YAAQCE4SAk2rQ7WaAQAATjZcBx4Bfx9vKhV9qBtQZ87GURRt2IHgrKNCnln+sZPyS5KwLapGvj2UXK2jmAWG2loGPwSgNSH3SG8mnSNWWj19l6Tw+LpVP76vxdp3rTyR4NdNJljk24sNAToYSRJbFsaJreC0fKMlT3lToglggxiVHNPlzoV8wpzzekRF2Akv3iO7Bl6RvyFFSwOCkTS2YpSLNepIqe7xxMbY3AKEQ7RkNqL8XN90jJrvazWlRcovAeCcc9rYI6z+0EnKLGSiCs56CleFS7q5LNvnfeXFlUES63BIN19WlDduuu7wi3s7nMUuzwOQM/PqjTrLk/w74BvuiMdvdnkBjmE49PXdbwi0rUpMBU0oJqgtbJqYHNyZI/BmkKfQAGP/IDMRmq6eHoHGSoogonMSmtuNEmyP1skZ4fBRmY/bMVg7YcX9qu9hF5GigN6QkrJJCPzcV7lA1T6D7cziKXhUF5ZYmH9LmPCxvqZo6MNZ~4604742~4600641',
    '_abck': '82179F3970B1C33CA4A13BA759A8DEE5~0~YAAQCE4SAmSrQ7WaAQAATzdcBw+9TtLByejgCe19ikhrVpscwclqOw6xbx92tfIxrc3NL4QO1MhpDSoepGFHiggutPgpG7ATEUcAZnvYCm8A615Tc3emOV5gSB6faxs0lh/DPQkBtqufh3GQmZDKEz6JboreoP35Bh9TttzHglbsuxbN05fxYscx4rSxdwzFOR4Tumdf3Id7TOpgr5UBXLxs4vxBzINJeqpLrO4qrC7vKnvECYrQ1ayVMQfh8bYonovl736Eq5/G4sgj4QRzA2aIPh6txAjF3BYw2VcVUnn6x1B25T9e5aSBFEcUib1xTf7WPDhP+IkEdOWJO7I2f50dZdCUWAC6jecUEC9wOpt5sMeFeD+CFPyGP0+pPXFbtiSUd7EOtnXmvxNZ3byGiNNKl6LpmOdU44F1Bjd6j0X0b3C5N2lS+qKHr3Y7Kiwfngj2ghbWFSV9q3TrEW/MHN1Dymdd5DnZh74NOQxEEVQNOuoPAGg8e2IGbz3bVbe3N34KPBSqoldxALfzcGmetC/N+lt4P1pZfXnpRnGaAaeqErmF0FqYaikUHOHVYekWMwch24AEy5q5nYuYMXQG5d1d4qalgQymIwpigyq6C3S66pYAyhO32d4gsaKs1gIj1JMpMPVy/R3rpQjsmvFB4NmBEvr6hZSIql00hxzTZWPM/TIntgm5xIqPYFG51xeA7ukjBIY=~-1~-1~1765357632~AAQAAAAE%2f%2f%2f%2f%2f+5DteXBLbFWXzJwwHojBid7qilKp9hYXvRAB9ZgIZ0N26o2XpCKdJ3NT82%2f0ca3XDrER3EQqxoUzTqRneJ82NB4y9wuv4NcOlCKXtRRx6mEJgtXCe9UvR3+m0Zu5gUkhYFGQb3cSXo3iF6OBsSVSmV3zeEfOlD5KWUf%2fm+QiQ%3d%3d~-1',
    'uws_session': '%7B%22start%22%3A1765350433353%2C%22count%22%3A12%2C%22referrer%22%3A%22%22%7D%7Csession_timeout',
    'uws_visitor': '%7B%22vid%22%3A%22176528217927232958%22%2C%22start%22%3A1765282179271%2C%22count%22%3A14%7D%7C1773131043380',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Wed+Dec+10+2025+09%3A24%3A03+GMT%2B0100+(Central+European+Standard+Time)&version=202408.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=f77116e0-fbb7-4a3f-9907-ccea659c6889&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=exp01%3A1%2CC0001%3A1%2Cadv01%3A1%2CV2STACK42%3A1&intType=1&geolocation=CZ%3B10&AwaitingReconsent=false',
    '_ga_H653QXESTP': 'GS2.1.s1765353432$o5$g0$t1765355043$j60$l0$h259178850',
    '_ga_EZ1BJ05B45': 'GS2.1.s1765353431$o5$g1$t1765355043$j60$l0$h232147316',
    'bm_lso': '41412D23DE19C64D856775FDE60F5BD1539CDF7A8658AFFC80E33D100362BFCF~YAAQCE4SAkurQ7WaAQAATjZcBwXokhlp/9AOPgijiBBkVDm0hQpVOlQZ+3D7Q4eis0JQhmhf3dFdYu2ewVY9kS/UnPijgLTpO2BAERFTsiLTbHGTxKBv2elytssNQis/200BjYvVpXY3leI4oobEmfwl33EJgCrry9Etp6YxsgnpqPKcdVd9QaFeHD6yA9b2RA5U5D4qTIuTDzWW+D9PIlxa1g6bPWoinkuGjygR2j4IosloOT0aL1VMv64LFcVWohL+zpIju+tNJ8xtSwcTP1evmWQuF/1pIdWLs/0werJG3y8R7+FBntIkKncXND0TvobysMHJ5JI+rgQ1RR+rJ9biX+Lr/18S9vkHy18zURFub9QAzZ50K+WkBPW1/U7JI+t6WjUHZqLzB7CxOd+K/nFtfwjHu8Vp2IFgfvix5dW+KqOjqp5dmXPSShlGUJIop4YXd4wdT98MhWwEEk5X^1765355043910',
    '_ga_H66GZMZXKX': 'GS2.1.s1765353431$o5$g1$t1765355044$j60$l0$h2135707429',
    'FPLC': 'nFQtm0xTS8WZaHlszyMhIBC2HYWCK48zY53J11Tke4CFjXlYMjpj19aBTQccr5aIFNHExW2MchL8Ws6EJIrQsipUmhukKv0OmhWg9O0uqke7IWNKueiO5PhbA6eyuA%3D%3D',
    'bm_sv': 'BD3276D3AE9E1E67E25CAA238B11516C~YAAQDZJkX2hGs6+aAQAACD5cBx5BLw+G6N/DgraaQRc3puvrnjkmqCrXaMI22J7sS6icMQ31cm6piHzYhYmt++dLOVo3iNzK4yIoXB6RphInC2WZwktOcIwsB9chDO1befQjkD8XGe5pG6rd197S6eFSmgk+yzP8Tpck09AtXFwqnfrKXHD0mK7nqAvIn3I3zDekYSCS5obv8B86cGE7c4yIXBJb1zc7zc01cadnMs7J8VtKpnoK7ScpLbCcTW4h~1',
    'akavpau_czech_vp': '1765355649~id=29c6ed7ada8d5110835cd674bea303c0',
}

# 2. Define the exact order of cookie keys
ordered_cookie_keys = [
    '_ait', 'aitHealthCheckDone', 'atrc', 'OptanonAlertBoxClosed', 
    'eupubconsent-v2', 'cookiePreferences', '_ga', '_gcl_au', 'FPAU', 
    '_csrf', 'uws_storage', 'AMCVS_E4860C0F53CE56C40A490D45%40AdobeOrg', 
    's_cc', 'bm_mi', 'ak_bmsc', 'uws_rate_comparators', 
    'AMCV_E4860C0F53CE56C40A490D45%40AdobeOrg', 's_gpv_pn', 'timestamp', 
    'bm_ss', 'bm_s', 'bm_so', 'bm_sz', '_abck', 'uws_session', 
    'uws_visitor', 'OptanonConsent', '_ga_H653QXESTP', '_ga_EZ1BJ05B45', 
    'bm_lso', '_ga_H66GZMZXKX', 'FPLC', 'bm_sv', 'akavpau_czech_vp'
]

# 3. Reconstruct the raw cookie header string to preserve order/formatting
raw_cookie_string = "; ".join([f"{key}={cookies_dict[key]}" for key in ordered_cookie_keys])

# 4. Define the headers, including the manually injected 'Cookie' header
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
    # Manually set the 'Cookie' header string
    'Cookie': raw_cookie_string
}
class TescoEnricher(BaseProductEnricher):
    def __init__(self):
        super().__init__(
            input_file=str(Path(__file__).parent.parent / 'data' / 'tesco_raw.json'),
            output_file=str(Path(__file__).parent.parent / 'data' / 'tesco_enriched.json'),
            num_workers=8
        )

    def get_product_info(self, product: Dict[str, Any]) -> Dict[str, Any]:
        product_url = product.get('product_url') or product.get('url')
        if not product_url:
            return {'nutrition': {}, 'allergies': {}, 'ingredients': None}

        # Extract ID
        try:
             product_id = product_url.rstrip('/').split('/')[-1]
        except Exception:
             logger.warning(f"Could not extract product ID from {product_url}")
             return {'nutrition': {}, 'allergies': {}, 'ingredients': None}

        api_url = f'https://nakup.itesco.cz/groceries/cs-CZ/products/{product_id}'
        # Use simple get with the global 'headers' defined above
        # Note: headers include cookies
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
             raise Exception(f"Non-200 status ({response.status_code}) for {product_id}")
        
        response.encoding = 'windows-1250'
        
        info = extract_product_info(response.text, product_id)
        
        if info.get('error'):
             logger.warning(f"Error for {product_id}: {info['error']}")
             return {'nutrition': {}, 'allergies': {}, 'ingredients': None}
             
        # Map to standard structure
        return {
            'nutrition': {}, # Not extracted by current script
            'allergies': {'Obsahuje': info.get('allergens', [])},
            'ingredients': " ".join(info.get('ingredients', []) or []) if isinstance(info.get('ingredients'), list) else info.get('ingredients'),
            'description': info.get('description')
        }

if __name__ == '__main__':
    enricher = TescoEnricher()
    enricher.enrich_products()
