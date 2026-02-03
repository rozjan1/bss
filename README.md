# BSS

A modular data pipeline for collecting, normalizing, and analyzing grocery product data from major supermarkets (currently Tesco, Billa, Albert). The system handles the complete ETL process—from raw HTML/API scraping to data normalization and visualization.

## Project Structure

```
bss/
├── data_collecting/
│   ├── data/               # Data storage (raw responses & processed JSON)
│   ├── scraper/            # Stage 1: Raw data acquisition
│   ├── processors/         # Stage 2: Data extraction and structuring
│   ├── enrichers/          # Stage 3: Third-party data augmentation
│   ├── normalization/      # Stage 4: Unit standardization and merging
│   ├── pipelines/          # Pipeline orchestration
│   └── utils/              # Shared utilities
├── frontend/               # Dockerized data viewer
├── pyproject.toml          # Project configuration
└── docker-compose.yml      # Frontend container configuration
```

## Setup

### Prerequisites

- **Python 3.14+**
- **[uv](https://github.com/astral-sh/uv)** (Package manager)
- **Docker** (Optional, for frontend)

### Installation

```bash
git clone <repository-url>
cd bss
uv sync
```

## Usage

### Data Pipeline

The pipeline is managed by `data_collecting/pipelines/run.py`.

**Execute full pipeline:**
```bash
uv run data_collecting/pipelines/run.py
```

**Execute specific stages:**
```bash
uv run data_collecting/pipelines/run.py --stage scrape
uv run data_collecting/pipelines/run.py --stage process
uv run data_collecting/pipelines/run.py --stage enrich
uv run data_collecting/pipelines/run.py --stage normalize
```

### Architecture

1.  **Scraping** (`scraper/`): Fetches and caches raw responses (HTML/JSON) in `data/raw/` to enable offline development and checkpoints.
2.  **Processing** (`processors/`): Parses raw cached data into structured product objects, removing duplicates.
3.  **Enriching** (`enrichers/`): Augments product data with nutritional values and allergens using external sources.
4.  **Normalization** (`normalization/`): Standardizes units (e.g., kJ/kcal), cleanses text, and merges datasets for the frontend.

### Frontend

Start the local viewer on port 8888:

```bash
docker compose up --build -d
```

## Extension

To add a new data source (e.g., `Kaufland`), implement the standard interfaces:

1.  **Scraper**: Inherit from `BaseScraper` in `scraper/kaufland_scraper.py`. Implement data fetching logic.
2.  **Processor**: Inherit from `BaseProcessor` in `processors/kaufland_processor.py`. Implement parsing logic.
3.  **Pipeline**: Register the new modules in `pipelines/run.py`.

## Data Lifecycle

`Source API` → `Scraper` (Raw Cache) → `Processor` (Structured JSON) → `Enricher` (Augmented JSON) → `Normalizer` (Final Dataset) → `Frontend`

