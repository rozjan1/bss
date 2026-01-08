import subprocess
import sys
from pathlib import Path
import time

# Define paths
BASE_DIR = Path(__file__).parent
SCRAPER_DIR = BASE_DIR / "scraper"
ENRICHER_DIR = BASE_DIR / "enrichers"
NORMALIZATION_DIR = BASE_DIR / "normalization"
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
    Runs all scrapers to collect data.
    """
    print("=== STAGE 1: SCRAPING ===")
    
    # List of scrapers to run
    scrapers = [
        #"albert_scraper.py", # Disabled since albert removed their online product listings
        "billa_scraper.py",
        "tesco_scraper.py"
    ]
    
    for scraper in scrapers:
        # Construct command: uv run <scraper_file>
        cmd = ["uv", "run", scraper]
        
        # Run the scraper in the scraper directory
        success = run_command(cmd, SCRAPER_DIR, f"Scraper: {scraper}")
        
        if not success:
            print(f"Warning: {scraper} failed, continuing with others...")

def run_enriching_stage():
    """
    Runs all enrichers to augment data.
    """
    print("=== STAGE 2: ENRICHING ===")
    
    enrichers = [
        # "enrich_albert_products.py", # Disabled since albert removed their online product listings
        "enrich_billa_products.py",
        "enrich_tesco_products.py"
    ]
    
    for enricher in enrichers:
        cmd = ["uv", "run", enricher]
        success = run_command(cmd, ENRICHER_DIR, f"Enricher: {enricher}")
        
        if not success:
            print(f"Warning: {enricher} failed, continuing with others...")
    print()

def run_normalization_stage():
    """
    Runs data normalization.
    """
    print("=== STAGE 3: NORMALIZATION ===")
    
    normalizer = "normalize_data.py"
    cmd = ["uv", "run", normalizer]
    
    run_command(cmd, NORMALIZATION_DIR, f"Normalizer: {normalizer}")
    print()

def main():
    print("Starting Data Pipeline...")
    print(f"Project Root: {BASE_DIR}")
    
    # Create the shared data directory
    DATA_DIR.mkdir(exist_ok=True)
    print(f"Ensured data directory exists at: {DATA_DIR}")

    print("-" * 30)
    
    run_scraping_stage()
    #run_enriching_stage()
    #run_normalization_stage()
    
    print("Pipeline execution completed.")

if __name__ == "__main__":
    main()
