# Advanced Filters Feature

## Overview
The BSS Supermarket Viewer now includes a comprehensive advanced filtering system that allows you to filter products by nutrition values, allergens, and ingredients.

## How to Use

### Opening Advanced Filters
Click the **"Advanced Filters"** button in the left sidebar (styled with a purple gradient).

### Filter Types

#### 1. Exclude Products With Allergens
- Check any allergens you want to avoid
- Products containing these allergens will be filtered out
- Add custom allergens by typing them in the input field and pressing Enter

#### 2. Must Be Free Of (Strict)
- Check allergens that products MUST NOT contain
- This is a stricter filter than "Exclude" - useful for severe allergies
- Add custom requirements by typing them in the input field and pressing Enter

#### 3. Exclude Ingredients
- Type specific ingredient names you want to avoid (e.g., "palm oil", "sugar", "gluten")
- Press Enter to add each ingredient
- Click the × button on any tag to remove it
- Searches are case-insensitive and accent-insensitive

#### 4. Nutrition Filters
- Set minimum and maximum values for any nutritional parameter
- Available filters include:
  - Energetická hodnota (kJ and kcal)
  - Tuky (fats)
  - Sacharidy (carbohydrates)
  - Cukry (sugars)
  - Bílkoviny (proteins)
  - Sůl (salt)
  - And any other nutrition values present in the products

### Applying Filters
1. Set your desired filters in the modal
2. Click **"Apply Filters"** to apply and close the modal
3. Click **"Clear All"** to reset all advanced filters

### How It Works
- All filters work together (AND logic)
- A product must pass ALL active filters to be shown
- Filters work alongside the basic filters (search, category, price range, sale only)
- The page resets to page 1 when filters are applied

## Technical Details

### Allergen Detection
- Extracts allergens from both object format (Albert) and array format
- Excludes items in the "Neobsahuje" (Does not contain) category
- Case-insensitive matching

### Nutrition Parsing
- Automatically extracts numeric values from nutrition strings
- Handles various formats: "1,5 g", "326 kJ", etc.
- Works with comma or period as decimal separator

### Ingredient Search
- Removes diacritics for better matching (e.g., "cukor" matches "cukr")
- Case-insensitive substring matching
- Searches the full ingredient text

## Examples

### Example 1: Gluten-Free, Low Sugar
1. Open Advanced Filters
2. In "Must Be Free Of", check "Pšenice" (wheat)
3. In "Exclude Ingredients", add "gluten"
4. In Nutrition Filters, set "Sacharidy" Max to 10
5. Apply Filters

### Example 2: High Protein, No Dairy
1. Open Advanced Filters
2. In "Exclude Products With Allergens", check "Mléko" (milk)
3. In Nutrition Filters, set "Bílkoviny" Min to 15
4. Apply Filters

### Example 3: Vegan Options
1. Open Advanced Filters
2. In "Must Be Free Of", check: Mléko, Vejce, Ryby
3. In "Exclude Ingredients", add: "med" (honey), "želatina" (gelatin)
4. Apply Filters

## Notes
- Not all products have complete nutrition/allergen data
- Products without the required data fields will be excluded from filtered results
- Custom allergen/ingredient entries persist until cleared
- Filters are client-side only - no server requests needed
