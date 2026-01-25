import json
import requests
from typing import Dict, Any, Optional
from loguru import logger
from pathlib import Path
from base_enricher import BaseProductEnricher

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

class BillaEnricher(BaseProductEnricher):
    def __init__(self):
        super().__init__(
            input_file=str(Path(__file__).parent.parent / 'data' / 'billa_processed.json'),
            output_file=str(Path(__file__).parent.parent / 'data' / 'billa_enriched.json'),
            num_workers=8
        )

    def get_product_info(self, product: Dict[str, Any]) -> Dict[str, Any]:
        product_url = product.get("product_url")
        if not product_url:
            return {'nutrition': {}, 'allergies': {}, 'ingredients': None}

        try:
            product_id = product_url.split("-")[-1]
            product_id = product_id[:2] + "-" + product_id[2:]
        except Exception:
            logger.warning(f"Could not extract product ID from {product_url}")
            return {'nutrition': {}, 'allergies': {}, 'ingredients': None}

        # Uses global COOKIES and HEADERS
        api_url = f"https://shop.billa.cz/api/product-discovery/products/{product_id}"
        response = requests.get(api_url, cookies=COOKIES, headers=HEADERS, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"Non-200 status ({response.status_code}) for {product_id}")
        
        product_data = response.json()
        return self._extract_product_details(product_data)

    def _extract_product_details(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug("Starting extract_product_details")
        additional_info = product_data.get("additionalInformation", [{}])
        food_info = additional_info[0].get("foodInformation", {})
        calculated_nutrition = food_info.get("calculatedNutrition", {})
        
        nutrition_output = {"Výživové údaje na": None}
        base_unit = calculated_nutrition.get("headers", {}).get("per100Header", "na 100g").replace("na ", "")
        nutrition_output["Výživové údaje na"] = base_unit.strip()

        nutrition_data = calculated_nutrition.get("data", [])
        
        for item in nutrition_data:
            name = item.get("name", "").strip()
            value = item.get("valuePer100", "").strip()

            if not name or not value:
                continue
                
            try:
                num_value = float(value)
                if name in ["KJ", "Energetická hodnota (kJ)"]:
                    nutrition_output["Energetická hodnota kJ"] = f"{int(num_value):,} kJ".replace(",", " ")
                elif name in ["Kcal", "Energetická hodnota (kcal)"]:
                    nutrition_output["Energetická hodnota kcal"] = f"{int(num_value):,} kcal".replace(",", " ")
                elif name in ["Tuky", "Tuky (g)"]:
                    nutrition_output["Tuky"] = f"{num_value:.1f} g".replace(".", ",")
                elif name in ["Z toho nasycené mastné kyseliny", " z toho nasycené (g)"]:
                    format_str = f"{num_value:.0f} g" if num_value == int(num_value) else f"{num_value:.1f} g"
                    nutrition_output["z toho nasycené mastné kyseliny"] = format_str.replace(".", ",")
                elif name in ["Sacharidy", "Sacharidy (g)"]:
                    nutrition_output["Sacharidy"] = f"{num_value:.1f} g".replace(".", ",")
                elif name in ["Z toho cukry", " z toho cukry (g)"]:
                    nutrition_output["z toho cukry"] = f"{num_value:.1f} g".replace(".", ",")
                elif name in ["Bílkoviny", "Bílkoviny (g)"]:
                    format_str = f"{num_value:.0f} g" if num_value == int(num_value) else f"{num_value:.1f} g"
                    nutrition_output["Bílkoviny"] = format_str.replace(".", ",")
                elif name in ["Sůl", "Sůl (g)"]:
                    nutrition_output["Sůl"] = f"{num_value:.2f} g".replace(".", ",")

            except ValueError:
                continue
        
        allergies_output = {
            "Obsahuje": [],
            "Neobsahuje": [],
            "Může obsahovat": [],
            "Inconnu": []
        }
        
        top_level_allergens = product_data.get("allergens", [])
        nested_allergens = [
            item.get("value1") for item in food_info.get("allergyAdvice", [])
        ]
        
        combined_allergens = set(
            [a.strip().capitalize() for a in top_level_allergens + nested_allergens if a]
        )
        
        sorted_allergens = sorted(list(combined_allergens))
        half_index = len(sorted_allergens) // 2
        allergies_output["Obsahuje"] = sorted_allergens[half_index:]
        
        ingredients_text = food_info.get("ingredientsText", "")
        ingredients_text_cleaned = ingredients_text.replace("<strong>", "").replace("</strong>", "").strip()

        return {
            "nutrition": nutrition_output,
            "allergies": allergies_output,
            "ingredients": ingredients_text_cleaned
        }

if __name__ == '__main__':
    enricher = BillaEnricher()
    enricher.enrich_products()