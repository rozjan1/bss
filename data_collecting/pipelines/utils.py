#!/usr/bin/env python3
"""
Pipeline utilities for managing and testing the data pipeline stages.

Provides convenient commands for:
- Running individual stages
- Checking pipeline status
- Cleaning outputs
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys


BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = BASE_DIR / "data" / "raw"  # Raw data now in data_collecting/data/raw/


def count_json_files(directory: Path) -> int:
    """Count JSON files in a directory."""
    if not directory.exists():
        return 0
    return len(list(directory.glob("*.json")))


def count_products_in_file(filepath: Path) -> int:
    """Count products in a JSON file."""
    if not filepath.exists():
        return 0
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return len(data) if isinstance(data, list) else 0
    except:
        return 0


def show_status():
    """Show the current status of the pipeline."""
    print("=" * 60)
    print("PIPELINE STATUS")
    print("=" * 60)
    
    sources = ["billa", "tesco"]
    
    for source in sources:
        print(f"\n{source.upper()}:")
        
        # Raw data
        raw_source_dir = RAW_DIR / source
        raw_count = count_json_files(raw_source_dir)
        print(f"  ├─ Raw files:      {raw_count:4d} files")
        
        # Processed data
        processed_file = DATA_DIR / f"{source}_processed.json"
        processed_count = count_products_in_file(processed_file)
        print(f"  ├─ Processed:      {processed_count:4d} products")
        
        # Enriched data
        enriched_file = DATA_DIR / f"{source}_enriched.json"
        enriched_count = count_products_in_file(enriched_file)
        print(f"  └─ Enriched:       {enriched_count:4d} products")
    
    print("\n" + "=" * 60)


def run_stage(stage: str, source: str = None):
    """Run a specific pipeline stage."""
    print(f"\nRunning stage: {stage.upper()}")
    print("-" * 60)
    
    if stage == "scrape":
        if source:
            subprocess.run(["uv", "run", f"{source}_scraper.py"], 
                         cwd=BASE_DIR / "scraper")
        else:
            subprocess.run(["uv", "run", "billa_scraper.py"], 
                         cwd=BASE_DIR / "scraper")
            subprocess.run(["uv", "run", "tesco_scraper.py"], 
                         cwd=BASE_DIR / "scraper")
    
    elif stage == "process":
        if source:
            subprocess.run(["uv", "run", f"{source}_processor.py"], 
                         cwd=BASE_DIR / "processors")
        else:
            subprocess.run(["uv", "run", "billa_processor.py"], 
                         cwd=BASE_DIR / "processors")
            subprocess.run(["uv", "run", "tesco_processor.py"], 
                         cwd=BASE_DIR / "processors")
    
    elif stage == "enrich":
        if source:
            if source == "billa":
                subprocess.run(["uv", "run", "enrich_billa_products.py"], 
                             cwd=BASE_DIR / "enrichers")
            elif source == "tesco":
                subprocess.run(["uv", "run", "enrich_tesco_openfoodfacts.py"], 
                             cwd=BASE_DIR / "enrichers")
        else:
            subprocess.run(["uv", "run", "enrich_billa_products.py"], 
                         cwd=BASE_DIR / "enrichers")
            subprocess.run(["uv", "run", "enrich_tesco_openfoodfacts.py"], 
                         cwd=BASE_DIR / "enrichers")
    
    elif stage == "normalize":
        subprocess.run(["uv", "run", "normalize_data.py"], 
                     cwd=BASE_DIR / "normalization")
    
    print("-" * 60)
    print("Stage completed!\n")


def clean_outputs(stage: str = None):
    """Clean output files from specified stage(s)."""
    print("\nCleaning outputs...")
    
    if stage == "raw" or stage is None:
        print("  - Removing raw data files...")
        for source_dir in RAW_DIR.iterdir():
            if source_dir.is_dir():
                for file in source_dir.glob("*.json"):
                    file.unlink()
    
    if stage == "processed" or stage is None:
        print("  - Removing processed files...")
        for file in DATA_DIR.glob("*_processed.json"):
            file.unlink()
    
    if stage == "enriched" or stage is None:
        print("  - Removing enriched files...")
        for file in DATA_DIR.glob("*_enriched.json"):
            file.unlink()
    
    print("Done!\n")


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline management utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Show pipeline status
        uv run pipeline_utils.py status
        
        # Run specific stage for all sources
        uv run pipeline_utils.py run scrape
        uv run pipeline_utils.py run process
        uv run pipeline_utils.py run enrich
        
        # Run specific stage for specific source
        uv run pipeline_utils.py run scrape --source billa
        uv run pipeline_utils.py run process --source tesco

        # Clean outputs
        uv run pipeline_utils.py clean --stage processed
        uv run pipeline_utils.py clean  # Clean all
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Status command
    subparsers.add_parser('status', help='Show pipeline status')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run a pipeline stage')
    run_parser.add_argument('stage', 
                           choices=['scrape', 'process', 'enrich', 'normalize'],
                           help='Stage to run')
    run_parser.add_argument('--source', 
                           choices=['billa', 'tesco'],
                           help='Run for specific source only')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean output files')
    clean_parser.add_argument('--stage',
                             choices=['raw', 'processed', 'enriched'],
                             help='Clean specific stage outputs')
    
    args = parser.parse_args()
    
    if args.command == 'status':
        show_status()
    elif args.command == 'run':
        run_stage(args.stage, args.source)
        show_status()
    elif args.command == 'clean':
        clean_outputs(args.stage)
        show_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
