import subprocess
import sys
import argparse
from pathlib import Path
import time

# Define paths
BASE_DIR = Path(__file__).parent.parent
SCRAPER_DIR = BASE_DIR / "scraper"
PROCESSOR_DIR = BASE_DIR / "processors"
ENRICHER_DIR = BASE_DIR / "enrichers"
DATA_DIR = BASE_DIR / "data"

def run_command(command, cwd, description):
    """
    Helper to run a subprocess command with timing and error handling.
    """
    print(f"--- Starting: {description} ---")
    start_time = time.time()
    try:
        # using uv run since thats what I use
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            text=True
        )
        duration = time.time() - start_time
        print(f"--- Finished: {description} in {duration:.2f}s ---\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"!!! Error in {description}: {e}")
        return False
    except FileNotFoundError:
        print(f"!!! Error: Command not found: {command[0]}")
        return False

def run_scraping_stage():
    """
    Runs all scrapers to collect raw API data.
    This stage ONLaY collects raw responses without processing.
    """
    print("=== STAGE 1: SCRAPING (Raw Data Collection) ===")
    
    # List of scrapers to run
    scrapers = [
        #"albert_scraper.py", # Disabled since albert removed their online product listings
        "billa_scraper.py",
        #"tesco_scraper.py"
    ]
    
    for scraper in scrapers:
        # Construct command: uv run <scraper_file>
        cmd = ["uv", "run", scraper]
        
        # Run the scraper in the scraper directory
        success = run_command(cmd, SCRAPER_DIR, f"Scraper: {scraper}")
        
        if not success:
            print(f"Warning: {scraper} failed, continuing with others...")
    print()

def run_processing_stage():
    """
    Runs all processors to extract structured data from raw responses.
    This stage transforms raw API responses into structured product data.
    """
    print("=== STAGE 2: PROCESSING (Data Extraction) ===")
    
    processors = [
        "billa_processor.py",
        #"tesco_processor.py"
    ]
    
    for processor in processors:
        cmd = ["uv", "run", processor]
        success = run_command(cmd, PROCESSOR_DIR, f"Processor: {processor}")
        
        if not success:
            print(f"Warning: {processor} failed, continuing with others...")
    print()

def run_enriching_stage():
    """
    Runs all enrichers to augment processed data with nutritional information.
    This stage adds nutrition, allergens, and ingredients from external APIs.
    """
    print("=== STAGE 3: ENRICHING (Nutritional Data) ===")
    
    enrichers = [
        # "enrich_albert_products.py", # Disabled since albert removed their online product listings
        "enrich_billa_products.py",
        #"enrich_tesco_products.py"
        #"enrich_tesco_openfoodfacts.py"
    ]
    
    for enricher in enrichers:
        cmd = ["uv", "run", enricher]
        success = run_command(cmd, ENRICHER_DIR, f"Enricher: {enricher}")
        
        if not success:
            print(f"Warning: {enricher} failed, continuing with others...")
    print()

def main():
    parser = argparse.ArgumentParser(description="Professional Data Pipeline Runner")
    parser.add_argument("--stage", choices=["scrape", "process", "enrich"], help="Run a specific stage only")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip the scraping stage")
    args = parser.parse_args()

    print("=" * 60)
    print("PROFESSIONAL DATA PIPELINE")
    print("=" * 60)
    print(f"Project Root: {BASE_DIR}")
    
    # Create the shared data directory
    DATA_DIR.mkdir(exist_ok=True)
    print(f"Data directory: {DATA_DIR}")
    print()

    print("Pipeline Stages:")
    print("  1. SCRAPING     - Collect raw API responses")
    print("  2. PROCESSING   - Extract structured data from raw responses")
    print("  3. ENRICHING    - Add nutritional information")
    print()
    print("-" * 60)
    
    if not args.stage or args.stage == "scrape":
        if not args.skip_scrape:
            run_scraping_stage()
    
    if not args.stage or args.stage == "process":
        run_processing_stage()
        
    if not args.stage or args.stage == "enrich":
        run_enriching_stage()
        
    
    print("=" * 60)
    print("Pipeline execution completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
