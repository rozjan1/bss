"""
Data normalization script for grocery product JSON files.

This script reads JSON files from frontend/data/*.json and normalizes:
1. Nutrition values - extracts numeric values as floats with units
2. Allergen structures - standardizes allergen data
3. Price data - ensures consistent numeric format
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class ProductNormalizer:
    """Normalizes product data from various grocery store sources."""
    
    # Common nutrition field mappings
    NUTRITION_FIELDS = {
        'energy_kj': ['Energetická hodnota kJ', 'Energetická hodnota (kJ)', 'Energy kJ'],
        'energy_kcal': ['Energetická hodnota kcal', 'Energetická hodnota (kcal)', 'Energy kcal', 'Energy'],
        'protein': ['Bílkoviny', 'Bílkoviny (g)', 'Protein'],
        'fat': ['Tuky', 'Tuky (g)', 'Fat'],
        'saturated_fat': ['z toho nasycené mastné kyseliny', 'Z toho nasycené mastné kyseliny', 'Saturated fat'],
        'carbohydrates': ['Sacharidy', 'Sacharidy (g)', 'Carbohydrates'],
        'sugar': ['z toho cukry', 'Z toho cukry', ' z toho cukry (g)', 'Sugar'],
        'fiber': ['Vláknina', 'Vláknina (g)', 'Fiber', 'Fibre'],
        'salt': ['Sůl', 'Sůl (g)', 'Salt'],
        'sodium': ['Sodík', 'Sodík (mg)', 'Sodium']
    }
    
    # Unit mappings
    UNIT_CONVERSIONS = {
        'kilogram': 'kg',
        'pieces': 'pcs',
        'kus': 'pcs'
    }
    
    def __init__(self):
        self.stats = {
            'total_products': 0,
            'normalized_products': 0,
            'nutrition_normalized': 0,
            'allergen_normalized': 0,
            'errors': []
        }
    
    def parse_numeric_value(self, value: Any) -> Tuple[Optional[float], Optional[str]]:
        """
        Parse a nutrition value and extract numeric value and unit.
        
        Args:
            value: Raw value (can be string like "7 g" or number)
            
        Returns:
            Tuple of (numeric_value, unit) or (None, None) if parsing fails
        """
        if value is None:
            return None, None
        
        if isinstance(value, (int, float)):
            return float(value), None
        
        if not isinstance(value, str):
            return None, None
        
        # Clean the string
        value = value.strip()
        if not value or value == '':
            return None, None
        
        # Try to extract number and unit
        # Patterns: "7 g", "1,5 g", "642 kJ", "153 kcal", "3.2 g"
        pattern = r'([\d.,]+)\s*([a-zA-Z]+)?'
        match = re.match(pattern, value)
        
        if match:
            number_str = match.group(1).replace(',', '.')  # Handle Czech decimal separator
            unit = match.group(2) if match.group(2) else None
            
            try:
                numeric_value = float(number_str)
                return numeric_value, unit
            except ValueError:
                return None, None
        
        return None, None
    
    def parse_price(self, price: Any) -> Optional[float]:
        """
        Parse price value and return as float.
        
        Args:
            price: Raw price value
            
        Returns:
            Float price or None
        """
        if price is None:
            return None
        
        if isinstance(price, (int, float)):
            return float(price)
        
        if isinstance(price, str):
            # Remove currency symbols and spaces
            cleaned = price.replace('Kč', '').replace('CZK', '').replace(' ', '')
            cleaned = cleaned.replace(',', '.')
            
            try:
                return float(cleaned)
            except ValueError:
                return None
        
        return None
    
    def normalize_nutrition(self, nutrition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize nutrition data to consistent format with floats and units.
        
        Args:
            nutrition: Raw nutrition dictionary
            
        Returns:
            Normalized nutrition dictionary
        """
        if not nutrition or not isinstance(nutrition, dict):
            return {}
        
        normalized = {}
        
        # Keep the serving size info if present
        if 'Výživové údaje na' in nutrition:
            normalized['per_serving'] = nutrition['Výživové údaje na']
        
        # Process each nutrition field
        for field_key, possible_names in self.NUTRITION_FIELDS.items():
            for name in possible_names:
                if name in nutrition:
                    value, unit = self.parse_numeric_value(nutrition[name])
                    if value is not None:
                        normalized[field_key] = {
                            'value': value,
                            'unit': unit or 'g'  # Default to grams if no unit specified
                        }
                        break
        
        return normalized
    
    def normalize_allergens(self, allergies: Any) -> Dict[str, Any]:
        """
        Normalize allergen data to consistent format.
        
        Args:
            allergies: Raw allergen data (can be dict, list, or other)
            
        Returns:
            Normalized allergen dictionary
        """
        if not allergies:
            return {
                'contains': [],
                'may_contain': [],
                'free_from': []
            }
        
        normalized = {
            'contains': [],
            'may_contain': [],
            'free_from': []
        }
        
        try:
            if isinstance(allergies, dict):
                # Handle dictionary format (Albert, Billa)
                if 'Obsahuje' in allergies and isinstance(allergies['Obsahuje'], list):
                    normalized['contains'] = [a for a in allergies['Obsahuje'] if a]
                
                if 'Může obsahovat' in allergies and isinstance(allergies['Může obsahovat'], list):
                    normalized['may_contain'] = [a for a in allergies['Může obsahovat'] if a]
                
                if 'Neobsahuje' in allergies and isinstance(allergies['Neobsahuje'], list):
                    normalized['free_from'] = [a for a in allergies['Neobsahuje'] if a]
            
            elif isinstance(allergies, list):
                # Handle list format - assume these are allergens present
                normalized['contains'] = [a for a in allergies if a]
        
        except Exception as e:
            self.stats['errors'].append(f"Allergen normalization error: {e}")
        
        return normalized
    
    def normalize_unit_code(self, unit_code: Optional[str]) -> Optional[str]:
        """
        Normalize unit codes to consistent format.
        
        Args:
            unit_code: Raw unit code
            
        Returns:
            Normalized unit code
        """
        if not unit_code:
            return None
        
        return self.UNIT_CONVERSIONS.get(unit_code, unit_code)
    
    def normalize_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a single product.
        
        Args:
            product: Raw product dictionary
            
        Returns:
            Normalized product dictionary
        """
        normalized = product.copy()
        
        try:
            # Normalize prices
            if 'original_price' in product:
                normalized['original_price'] = self.parse_price(product['original_price'])
            
            if 'sale_price' in product:
                normalized['sale_price'] = self.parse_price(product['sale_price'])
            
            if 'original_ppu' in product:
                normalized['original_ppu'] = self.parse_price(product['original_ppu'])
            
            if 'sale_ppu' in product:
                normalized['sale_ppu'] = self.parse_price(product['sale_ppu'])
            
            # Determine primary price for convenience
            sale_val = normalized.get('sale_price')
            orig_val = normalized.get('original_price')
            normalized['price'] = sale_val if sale_val is not None else orig_val
            
            # Normalize unit code
            if 'unit_code' in product:
                normalized['unit_code'] = self.normalize_unit_code(product['unit_code'])
            
            # Normalize nutrition
            if 'nutrition' in product:
                normalized['nutrition'] = self.normalize_nutrition(product['nutrition'])
                if normalized['nutrition']:
                    self.stats['nutrition_normalized'] += 1
            
            # Normalize allergens
            if 'allergies' in product:
                normalized['allergies'] = self.normalize_allergens(product['allergies'])
                self.stats['allergen_normalized'] += 1
            
            self.stats['normalized_products'] += 1
            
        except Exception as e:
            self.stats['errors'].append(f"Product normalization error for '{product.get('item_name', 'unknown')}': {e}")
        
        return normalized
    
    def process_file(self, input_path: Path, output_path: Path) -> None:
        """
        Process a single JSON file.
        
        Args:
            input_path: Input JSON file path
            output_path: Output JSON file path
        """
        print(f"Processing {input_path.name}...")
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            if not isinstance(products, list):
                print(f"Warning: {input_path.name} does not contain a list of products")
                return
            
            normalized_products = []
            for product in products:
                self.stats['total_products'] += 1
                normalized = self.normalize_product(product)
                normalized_products.append(normalized)
            
            # Write normalized data
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(normalized_products, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Normalized {len(normalized_products)} products from {input_path.name}")
        
        except Exception as e:
            print(f"✗ Error processing {input_path.name}: {e}")
            self.stats['errors'].append(f"File processing error for {input_path.name}: {e}")
    
    def process_all(self, input_dir: Path, output_dir: Path) -> None:
        """
        Process all JSON files in the input directory.
        
        Args:
            input_dir: Directory containing input JSON files
            output_dir: Directory for output JSON files
        """
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all JSON files
        json_files = list(input_dir.glob('*_enriched.json'))
        
        if not json_files:
            print(f"No enriched JSON files found in {input_dir}")
            return
        
        print(f"\nFound {len(json_files)} enriched JSON files to process")
        print("=" * 60)
        
        for json_file in json_files:
            output_file = output_dir / json_file.name
            self.process_file(json_file, output_file)
        
        print("\n" + "=" * 60)
        print("NORMALIZATION COMPLETE")
        print("=" * 60)
        print(f"Total products processed: {self.stats['total_products']}")
        print(f"Successfully normalized: {self.stats['normalized_products']}")
        print(f"Nutrition data normalized: {self.stats['nutrition_normalized']}")
        print(f"Allergen data normalized: {self.stats['allergen_normalized']}")
        
        if self.stats['errors']:
            print(f"\n⚠ Errors encountered: {len(self.stats['errors'])}")
            print("First 5 errors:")
            for error in self.stats['errors'][:5]:
                print(f"  - {error}")


def main():
    """Main function to run normalization."""
    # Setup paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # Input: Read from the intermediate data_collecting/data folder
    input_dir = project_root / 'data_collecting' / 'data'
    
    # Output: Write to the frontend/data folder for the app to use
    output_dir = project_root / 'frontend' / 'data'
    
    print("Product Data Normalization Script")
    print("=" * 60)
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    # Create normalizer and process files
    normalizer = ProductNormalizer()
    normalizer.process_all(input_dir, output_dir)
    
    print("\n✓ All files processed successfully!")


if __name__ == '__main__':
    main()
