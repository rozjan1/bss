import subprocess
import sys
from pathlib import Path
import time

# Define paths
BASE_DIR = Path(__file__).parent
SCRAPER_DIR = BASE_DIR / "scraper"

def run_command(command, cwd, description):
    """
    Helper to run a subprocess command with timing and error handling.
    """
    print(f"--- Starting: {description} ---")
    start_time = time.time()
    try:
        # We use 'uv run' to execute the scripts, matching the user's workflow
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
        f.name for f in SCRAPER_DIR.glob("*_scraper.py")
        if f.name != "base_scraper.py"
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
    Placeholder for data enriching stage.
    """
    print("=== STAGE 2: ENRICHING (Future) ===")
    # TODO: Implement enriching logic
    # Example:
    # cmd = ["uv", "run", "enrich_data.py"]
    # run_command(cmd, ENRICHER_DIR, "Data Enricher")
    print("Skipping enriching stage (not implemented yet)...")
    print()

def run_normalization_stage():
    """
    Placeholder for data normalization stage.
    """
    print("=== STAGE 3: NORMALIZATION (Future) ===")
    # TODO: Implement normalization logic
    # Example:
    # cmd = ["uv", "run", "normalize_data.py"]
    # run_command(cmd, NORMALIZATION_DIR, "Data Normalizer")
    print("Skipping normalization stage (not implemented yet)...")
    print()

def main():
    print("Starting Data Pipeline...")
    print(f"Project Root: {BASE_DIR}")
    print("-" * 30)
    
    run_scraping_stage()
    run_enriching_stage()
    run_normalization_stage()
    
    print("Pipeline execution completed.")

if __name__ == "__main__":
    main()
