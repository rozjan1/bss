"""
OpenFoodFacts utility for fetching product information by barcode.

This module provides a simple interface to the OpenFoodFacts API,
allowing enrichers to fetch nutrition, allergen, and ingredient data
for products with barcodes.
"""

import requests
from typing import Dict, Any, Optional
from loguru import logger


class OpenFoodFactsFetcher:
    """Fetch product information from OpenFoodFacts API using barcode."""
    
    BASE_URL = "https://world.openfoodfacts.org/api/v2/product"
    
    def __init__(self, timeout: int = 10):
        """
        Initialize the OpenFoodFacts fetcher.
        
        Args:
            timeout: Request timeout in seconds (default: 10)
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ProductEnricher/1.0 (Educational Project)'
        })
    
    def fetch(self, barcode: str) -> Dict[str, Any]:
        """
        Fetch product information from OpenFoodFacts API.
        
        Args:
            barcode: Product barcode (EAN/UPC code)
            
        Returns:
            Dict with 'nutrition', 'allergies', 'ingredients'
            
        Raises:
            ValueError: If barcode is invalid
            Exception: If the API request fails or product not found
        """
        # Clean barcode - remove any non-digit characters
        barcode_clean = ''.join(c for c in str(barcode) if c.isdigit())
        
        if not barcode_clean:
            raise ValueError(f"Invalid barcode: {barcode}")
        
        url = f"{self.BASE_URL}/{barcode_clean}.json"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if product was found
            if data.get('status') != 1:
                raise Exception(f"Product not found in OpenFoodFacts: {barcode_clean}")
            
            product = data.get('product', {})
            
            return self._parse_product_data(product)
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch from OpenFoodFacts: {e}")
    
    def _parse_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Parse OpenFoodFacts product data into our format."""
        
        # Extract nutrition information
        nutrition = self._extract_nutrition(product)
        
        # Extract allergens
        allergies = self._extract_allergens(product)
        
        # Extract ingredients
        ingredients = self._extract_ingredients(product)
        
        return {
            'nutrition': nutrition,
            'allergies': allergies,
            'ingredients': ingredients
        }
    
    def _extract_nutrition(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format nutrition data."""
        nutriments = product.get('nutriments', {})
        
        if not nutriments:
            return {}
        
        nutrition_output = {}
        
        # Serving size / base unit
        serving_size = product.get('nutrition_data_per', '100g')
        if serving_size:
            nutrition_output["Výživové údaje na"] = serving_size
        
        # Energy in kJ
        energy_kj = nutriments.get('energy-kj_100g') or nutriments.get('energy_100g')
        if energy_kj is not None:
            nutrition_output["Energetická hodnota kJ"] = f"{int(energy_kj):,} kJ".replace(",", " ")
        
        # Energy in kcal
        energy_kcal = nutriments.get('energy-kcal_100g')
        if energy_kcal is not None:
            nutrition_output["Energetická hodnota kcal"] = f"{int(energy_kcal):,} kcal".replace(",", " ")
        
        # Fat
        fat = nutriments.get('fat_100g')
        if fat is not None:
            nutrition_output["Tuky"] = f"{fat:.1f} g".replace(".", ",")
        
        # Saturated fat
        saturated_fat = nutriments.get('saturated-fat_100g')
        if saturated_fat is not None:
            nutrition_output["z toho nasycené mastné kyseliny"] = f"{saturated_fat:.1f} g".replace(".", ",")
        
        # Carbohydrates
        carbs = nutriments.get('carbohydrates_100g')
        if carbs is not None:
            nutrition_output["Sacharidy"] = f"{carbs:.1f} g".replace(".", ",")
        
        # Sugars
        sugars = nutriments.get('sugars_100g')
        if sugars is not None:
            nutrition_output["z toho cukry"] = f"{sugars:.1f} g".replace(".", ",")
        
        # Protein
        protein = nutriments.get('proteins_100g')
        if protein is not None:
            nutrition_output["Bílkoviny"] = f"{protein:.1f} g".replace(".", ",")
        
        # Salt
        salt = nutriments.get('salt_100g')
        if salt is not None:
            nutrition_output["Sůl"] = f"{salt:.2f} g".replace(".", ",")
        
        # Fiber (optional, not always present in other enrichers)
        fiber = nutriments.get('fiber_100g')
        if fiber is not None:
            nutrition_output["Vláknina"] = f"{fiber:.1f} g".replace(".", ",")
        
        return nutrition_output
    
    def _extract_allergens(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format allergen information."""
        allergies_output = {
            "Obsahuje": [],
            "Může obsahovat": []
        }
        
        # Get allergens from various fields
        allergens_str = product.get('allergens', '')
        allergens_tags = product.get('allergens_tags', [])
        traces_tags = product.get('traces_tags', [])
        
        # Process allergen tags (format: en:milk -> Milk)
        contains = []
        for tag in allergens_tags:
            if tag and ':' in tag:
                allergen = tag.split(':', 1)[1].replace('-', ' ').capitalize()
                contains.append(allergen)
            elif tag:
                contains.append(tag.capitalize())
        
        # Process traces (may contain)
        may_contain = []
        for tag in traces_tags:
            if tag and ':' in tag:
                allergen = tag.split(':', 1)[1].replace('-', ' ').capitalize()
                may_contain.append(allergen)
            elif tag:
                may_contain.append(tag.capitalize())
        
        # Also try to parse allergens string
        if allergens_str and not contains:
            # Split by common separators
            allergen_parts = allergens_str.replace(',', ';').split(';')
            for part in allergen_parts:
                part = part.strip()
                if part and ':' in part:
                    allergen = part.split(':', 1)[1].strip().capitalize()
                    if allergen:
                        contains.append(allergen)
                elif part:
                    contains.append(part.capitalize())
        
        allergies_output["Obsahuje"] = sorted(list(set(contains)))
        allergies_output["Může obsahovat"] = sorted(list(set(may_contain)))
        
        return allergies_output
    
    def _extract_ingredients(self, product: Dict[str, Any]) -> Optional[str]:
        """Extract ingredients text, preferring Czech language."""
        # Try Czech first, then fall back to other languages
        ingredients = (
            product.get('ingredients_text_cs') or
            product.get('ingredients_text_sk') or  # Slovak is similar
            product.get('ingredients_text_en') or
            product.get('ingredients_text') or
            None
        )
        
        if ingredients:
            # Clean up HTML if present
            ingredients = ingredients.replace('<strong>', '').replace('</strong>', '')
            ingredients = ingredients.replace('<b>', '').replace('</b>', '')
            ingredients = ingredients.strip()
        
        return ingredients if ingredients else None


# Convenience function for one-off fetches
def fetch_product_by_barcode(barcode: str) -> Dict[str, Any]:
    """
    Convenience function to fetch a product by barcode.
    
    Args:
        barcode: Product barcode (EAN/UPC code)
        
    Returns:
        Dict with 'nutrition', 'allergies', 'ingredients'
        
    Raises:
        ValueError: If barcode is invalid
        Exception: If the API request fails or product not found
    """
    fetcher = OpenFoodFactsFetcher()
    return fetcher.fetch(barcode)
