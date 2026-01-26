from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict

class NutritionInfo(BaseModel):
    serving_size: Optional[str] = Field(None, alias="Serving Size")
    energy_kj: Optional[str] = None
    energy_kcal: Optional[str] = None
    fat: Optional[str] = None
    saturated_fat: Optional[str] = None
    carbohydrates: Optional[str] = None
    sugars: Optional[str] = None
    protein: Optional[str] = None
    salt: Optional[str] = None

class Product(BaseModel):
    source: str
    product_category: str
    item_name: str
    image_url: Optional[HttpUrl] = None
    original_price: float
    original_ppu: Optional[float] = None
    sale_price: float
    sale_ppu: Optional[float] = None
    unit_code: Optional[str] = None
    product_url: HttpUrl
    sale_requirement: Optional[str] = None # e.g., "tesco_clubcard", "billa_card"
    gtin: Optional[str] = None  # Barcode/GTIN for product identification
    
    # These fields can be populated later by your enrichers
    ingredients: Optional[str] = None
    nutrition: Optional[NutritionInfo] = None
    allergens: List[str] = []