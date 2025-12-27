# BSS Supermarket Viewer - Usage Examples

## Quick Start Guide

The BSS Supermarket Viewer now supports advanced filtering and nutrition-based sorting, allowing you to find exactly what you need.

## Example Use Cases

### Example 1: High Protein Products Under 200 Kč
**Goal:** Find products with the most protein that cost less than 200 Kč

**Steps:**
1. In the **Price range** field, set Max to `200`
2. In the **Sort** dropdown (top bar), select `Most Protein`
3. Click **Apply**

**Result:** Products are filtered to show only items under 200 Kč, sorted by protein content (highest first)

---

### Example 2: Low-Calorie Products Without Dairy
**Goal:** Find products with least energy that don't contain milk/dairy

**Steps:**
1. Click **Advanced Filters**
2. In "Exclude Products With Allergens" section, check `Mléko` (milk)
3. Click **Apply Filters**
4. In the **Sort** dropdown, select `Least Energy (kcal)`

**Result:** Dairy-free products sorted by lowest calories first

---

### Example 3: High Protein, Low Carb, Under 150 Kč
**Goal:** Find high-protein, low-carb products within budget

**Steps:**
1. Set **Price Max** to `150`
2. Click **Advanced Filters**
3. In the "Nutrition Filters" section:
   - Set `Bílkoviny` (Protein) Min to `15`
   - Set `Sacharidy` (Carbs) Max to `10`
4. Click **Apply Filters**
5. In **Sort** dropdown, select `Most Protein`

**Result:** Products with at least 15g protein, max 10g carbs, under 150 Kč, sorted by protein content

---

### Example 4: Vegan High-Protein Options
**Goal:** Find vegan protein sources sorted by protein content

**Steps:**
1. Click **Advanced Filters**
2. In "Must Be Free Of (Strict)":
   - Check `Mléko` (milk)
   - Check `Vejce` (eggs)
   - Check `Ryby` (fish)
3. In "Exclude Ingredients":
   - Type `med` (honey) and press Enter
   - Type `želatina` (gelatin) and press Enter
4. Click **Apply Filters**
5. In **Sort** dropdown, select `Most Protein`

**Result:** Vegan products sorted by highest protein content

---

### Example 5: Low-Sugar Products Without Palm Oil
**Goal:** Find products with minimal sugar that don't contain palm oil

**Steps:**
1. Click **Advanced Filters**
2. In "Exclude Ingredients":
   - Type `palmový olej` and press Enter
   - Type `palm oil` and press Enter
3. In "Nutrition Filters":
   - Set `z toho cukry` (Sugar) Max to `5`
4. Click **Apply Filters**
5. In **Sort** dropdown, select `Least Sugar`

**Result:** Products with max 5g sugar, no palm oil, sorted by lowest sugar first

---

### Example 6: Low-Sodium Products on Sale
**Goal:** Find discounted products with low salt content

**Steps:**
1. Check **Only on sale** checkbox
2. Click **Advanced Filters**
3. In "Nutrition Filters":
   - Set `Sůl` (Salt) Max to `0.5`
4. Click **Apply Filters**
5. In **Sort** dropdown, select `Least Salt`

**Result:** Only sale items with max 0.5g salt, sorted by lowest salt content

---

### Example 7: Gluten-Free Low-Fat Options
**Goal:** Find gluten-free products with minimal fat

**Steps:**
1. Click **Advanced Filters**
2. In "Must Be Free Of (Strict)":
   - Check `Pšenice` (wheat)
   - Type `gluten` in custom field and press Enter
3. In "Nutrition Filters":
   - Set `Tuky` (Fat) Max to `3`
4. Click **Apply Filters**
5. In **Sort** dropdown, select `Least Fat`

**Result:** Gluten-free products with max 3g fat, sorted by lowest fat first

---

## Tips & Tricks

### Combining Filters
- All filters work together (AND logic)
- You can use basic filters (price, category, search) + advanced filters + sorting simultaneously
- Example: Search for "chicken" + Price under 100 Kč + Sort by Most Protein

### Active Filters Badge
- The **Advanced Filters** button shows a red badge with the number of active advanced filters
- Example: `Advanced Filters (5)` means 5 advanced filters are active
- Click **Clear All** in the advanced filters modal to reset

### Nutrition Sorting
The following nutrition sorts are available:
- **Most/Least Protein** - For high-protein diets
- **Most/Least Energy (kcal)** - For calorie management
- **Most/Least Fat** - For low-fat or high-fat diets
- **Most/Least Carbs** - For low-carb diets
- **Most/Least Sugar** - For sugar management
- **Most/Least Salt** - For sodium management

### Search + Sort + Filter
Power user workflow:
1. Use the search bar for keywords (e.g., "chicken breast")
2. Set price range
3. Open Advanced Filters for allergen/ingredient exclusions
4. Sort by desired nutrition value
5. Browse results!

### Missing Data
- Products without nutrition data will appear at the end when sorting by nutrition
- Products without allergen data won't be filtered by allergen filters
- Use the "Informace" button on each product card to see available details

---

## Common Queries

**Q: How do I find the cheapest high-protein products?**
A: Sort by "Most Protein", then look at the first few pages - they'll show the highest protein options, and you can scan for the lowest prices.

**Q: Can I exclude multiple ingredients at once?**
A: Yes! In the "Exclude Ingredients" section, type each ingredient and press Enter. They'll appear as removable tags.

**Q: How do I find products suitable for allergies?**
A: Use "Must Be Free Of (Strict)" for severe allergies. This ensures products are completely free of those allergens.

**Q: Can I save my filter preferences?**
A: Currently filters reset on page reload. Keep your common filters noted or use browser bookmarks with URL parameters (feature coming soon).

---

## Keyboard Shortcuts
- **Enter** in ingredient/allergen fields: Add item to list
- **Click × on tags**: Remove ingredient exclusion
- **Escape** (when modal open): Close modal

---

## Best Practices

1. **Start broad, then narrow**: Begin with sorting, then add filters
2. **Use "Must Be Free Of" for allergies**: More strict than "Exclude"
3. **Combine price with nutrition**: Find the best value for your dietary needs
4. **Check product details**: Click "Informace" to verify nutrition/allergen info
5. **Clear filters between searches**: Use "Clear All" to start fresh

---

Happy shopping! 🛒
