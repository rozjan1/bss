# BSS - Supermarket Data Pipeline

A comprehensive data collection pipeline for scraping, processing, enriching, and normalizing product data from various supermarkets (Tesco, Billa, Albert, etc.). The project includes a full backend pipeline and a dockerized frontend for viewing the collected data.

## 📂 Project Structure

```
bss/
├── data_collecting/
│   ├── data/               # Stores raw and processed JSON data
│   │   └── raw/            # Raw API/HTML responses saved during scraping
│   ├── scraper/            # Stage 1: Scrapers (Raw Data Collection)
│   ├── processors/         # Stage 2: Processors (Data Extraction)
│   ├── enrichers/          # Stage 3: Enrichers (Nutrition/Allergens)
│   ├── normalization/      # Stage 4: Normalization (Standardization)
│   ├── pipelines/          # Orchestration scripts (run.py)
│   └── utils/              # Helper utilities
├── frontend/               # Static web viewer (Dockerized)
├── pyproject.toml          # Python project configuration
├── uv.lock                 # Dependency lock file
└── docker-compose.yml      # Docker composition for frontend
```

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.14+
- **[uv](https://github.com/astral-sh/uv)**: Extremely fast Python package installer and resolver.
- **Docker**: For running the frontend viewer.

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd bss
   ```

2. Sync dependencies using `uv`:
   ```bash
   uv sync
   ```

## 🛠️ Usage

### Running the Data Pipeline

The project uses a central orchestration script to manage the data pipeline stages.

**Run the full pipeline:**
```bash
uv run data_collecting/pipelines/run.py
```

**Run specific stages:**

You can flag specific stages to run individually:
```bash
# Run only scraping
uv run data_collecting/pipelines/run.py --stage scrape

# Run only processing
uv run data_collecting/pipelines/run.py --stage process

# Run only enriching
uv run data_collecting/pipelines/run.py --stage enrich

# Run only normalization
uv run data_collecting/pipelines/run.py --stage normalize
```

### Pipeline Stages Explained

1.  **Scraping** (`data_collecting/scraper/`):
    *   Fetches raw data from supermarket APIs or websites.
    *   Saves raw responses (JSON/HTML) to `data_collecting/data/raw/` to avoid re-scraping during development.
    *   Supports checkpoints to resume interrupted scrapes.

2.  **Processing** (`data_collecting/processors/`):
    *   Reads raw files from `data/raw/`.
    *   Extracts structured information (price, name, image, ID).
    *   Removes duplicates.
    *   Outputs specific processed JSON files (e.g., `tesco_products.json`).

3.  **Enriching** (`data_collecting/enrichers/`):
    *   Takes processed files and requests additional details (Nutrition, Ingredients, Allergens).
    *   Uses multi-threading for speed.
    *   Outputs enriched files (e.g., `tesco_enriched.json`).

4.  **Normalization** (`data_collecting/normalization/`):
    *   Standardizes units (kJ/kcal, g/kg).
    *   Normalizes allergen naming conventions.
    *   Merges data into a final format for the frontend.

---

### Running the Frontend

To view the collected data:

```bash
docker compose up --build frontend
```

Then open your browser at **http://localhost:8888** (port configured in `docker-compose.yml`).

---

## ➕ How to Add a New Supermarket

To add a new supermarket (e.g., "Kaufland"), follow this pattern:

### 1. Create a Scraper
Create `data_collecting/scraper/kaufland_scraper.py` inheriting from `BaseScraper`.

```python
from .base_scraper import BaseScraper

class KauflandScraper(BaseScraper):
    def __init__(self):
        super().__init__("kaufland")
    
    def fetch_category(self, category_code, page):
        # Implement API call or HTML request
        pass
    
    # data is automatically saved to data/raw/kaufland/
```

### 2. Create a Processor
Create `data_collecting/processors/kaufland_processor.py` inheriting from `BaseProcessor`.

```python
from .base_processor import BaseProcessor

class KauflandProcessor(BaseProcessor):
    def __init__(self):
        super().__init__("kaufland") # Matches source_name above

    def parse_response(self, response_data, category_name):
        # Extract products from raw JSON/HTML
        return [Product(...), Product(...)]
```

### 3. Create an Enricher (Optional)
If specific nutrition fetching is needed, create `data_collecting/enrichers/enrich_kaufland.py` inheriting from `BaseProductEnricher`.

### 4. Register in Pipeline
Edit `data_collecting/pipelines/run.py`:

```python
def run_scraping_stage():
    scrapers = [
        "tesco_scraper.py",
        "kaufland_scraper.py"  # <-- Add this
    ]

def run_processing_stage():
    processors = [
        "tesco_processor.py",
        "kaufland_processor.py" # <-- Add this
    ]
```

## 📊 Data Flow

1. **Input**: Supermarket API/Website
2. **Scraper** -> `data/raw/source_name/*.json`
3. **Processor** -> `data/source_name.json`
4. **Enricher** -> `data/source_name_enriched.json`
5. **Normalizer** -> `frontend/products.json`
6. **Output**: Frontend Viewer
