"""
Main entry point for the Apify actor using Python
Adapted to work with Apify's Python Docker image
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("news_scraper")

# Add parent directory to path to allow imports from scraper package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our scraper modules
from scraper.site_scrapers import get_scraper_for_url



# Add this near the beginning of the main() function:
logger.info("Checking for input...")
logger.info(f"Environment variables: APIFY_IS_AT_HOME={os.environ.get('APIFY_IS_AT_HOME')}")
logger.info(f"Input environment variable: {os.environ.get('APIFY_INPUT')}")

# Try direct environment variable first
input_env = os.environ.get("APIFY_INPUT")
if input_env:
    logger.info(f"Found input in APIFY_INPUT: {input_env}")
    try:
        actor_input = json.loads(input_env)
    except Exception as e:
        logger.error(f"Error parsing APIFY_INPUT: {str(e)}")
else:
    logger.info("No APIFY_INPUT found, checking file paths...")

# Check multiple possible input paths
possible_paths = [
    "apify_storage/key_value_stores/default/INPUT.json",
    "key_value_stores/default/INPUT.json",
    os.path.join(os.environ.get("APIFY_INPUT_KEY", ""), "INPUT.json"),
    os.path.join(os.environ.get("APIFY_INPUT_KEY", ""), "key_value_stores", os.environ.get("APIFY_DEFAULT_KEY_VALUE_STORE_ID", "default"), "INPUT.json")
]

for path in possible_paths:
    logger.info(f"Checking path: {path}")
    if os.path.exists(path):
        logger.info(f"Found input file at: {path}")
        try:
            with open(path, "r") as f:
                actor_input = json.load(f)
                break
        except Exception as e:
            logger.error(f"Error reading input file {path}: {str(e)}")






async def main():
    """Main entry point for the Apify actor"""
    
    logger.info("Starting News Scraper Actor")
    
    # Get the input from environment variables or file
    try:
        # Check if running on Apify platform
        if os.environ.get("APIFY_IS_AT_HOME"):
            # Get input from the default key-value store
            input_path = os.path.join(
                os.environ.get("APIFY_INPUT_KEY") or "INPUT", 
                "key_value_stores", 
                os.environ.get("APIFY_DEFAULT_KEY_VALUE_STORE_ID"), 
                "INPUT.json"
            )
            
            if os.path.exists(input_path):
                with open(input_path, "r") as f:
                    actor_input = json.load(f)
            else:
                # Try environment variable
                input_env = os.environ.get("APIFY_INPUT")
                if input_env:
                    actor_input = json.loads(input_env)
                else:
                    actor_input = {}
        else:
            # Local development - use test input
            actor_input = {
                "urls": [
                    "https://www.al-monitor.com/search?text=iraq+oil",
                    "https://africanreview.com/search?q=iraq+oil&Search="
                ],
                "query": "iraq oil",
                "maxPages": 1
            }
    except Exception as e:
        logger.error(f"Error reading input: {str(e)}")
        actor_input = {}
    
    # Extract parameters from input
    urls = actor_input.get('urls', [])
    query = actor_input.get('query', 'iraq oil')
    max_pages = actor_input.get('maxPages', 1)
    
    # If a single URL is provided as a string, convert it to a list
    if isinstance(urls, str):
        urls = [urls]
        
    # If no URLs are provided, log an error and exit
    if not urls:
        logger.error("No URLs provided in the input")
        return
        
    # Create output directory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each URL
    all_results = []
    
    for url in urls:
        logger.info(f"Processing URL: {url}")
        
        try:
            # Get the appropriate scraper for the URL
            scraper = get_scraper_for_url(url, output_dir)
            
            # Check if it's a Playwright or Requests scraper
            if hasattr(scraper, 'scrape'):
                if asyncio.iscoroutinefunction(scraper.scrape):
                    # Playwright scraper
                    logger.info(f"Using Playwright scraper for {url}")
                    results = await scraper.scrape(query, max_pages)
                else:
                    # Requests scraper
                    logger.info(f"Using Requests scraper for {url}")
                    results = scraper.scrape(query, max_pages)
                    
                # Save results to dataset
                if results:
                    logger.info(f"Scraped {len(results)} results from {url}")
                    
                    # Add results to the overall collection
                    for result in results:
                        result['source_url'] = url
                        all_results.append(result)
                else:
                    logger.warning(f"No results found for {url}")
            else:
                logger.error(f"No scraper implementation found for {url}")
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
            continue
            
    # Log the summary
    logger.info(f"Total results scraped: {len(all_results)}")
    
    # Save all results to a single JSON file
    if all_results:
        output = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "max_pages": max_pages,
            "total_results": len(all_results),
            "articles": all_results
        }
        
        # Save to output file
        output_path = os.path.join(output_dir, "OUTPUT.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        logger.info(f"Results saved to {output_path}")
        
        # If running on Apify, save to the default dataset
        if os.environ.get("APIFY_IS_AT_HOME"):
            dataset_dir = os.path.join(
                os.environ.get("APIFY_DATASETS_DIR", ""),
                os.environ.get("APIFY_DEFAULT_DATASET_ID", "default")
            )
            os.makedirs(dataset_dir, exist_ok=True)
            
            # Save each article as a separate item in the dataset
            for i, article in enumerate(all_results):
                item_path = os.path.join(dataset_dir, f"{i}.json")
                with open(item_path, "w", encoding="utf-8") as f:
                    json.dump(article, f, ensure_ascii=False)
            
            # Save the full output to the key-value store
            kv_store_dir = os.path.join(
                os.environ.get("APIFY_KEY_VALUE_STORES_DIR", ""),
                os.environ.get("APIFY_DEFAULT_KEY_VALUE_STORE_ID", "default")
            )
            os.makedirs(kv_store_dir, exist_ok=True)
            
            kv_output_path = os.path.join(kv_store_dir, "OUTPUT.json")
            with open(kv_output_path, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            logger.info(f"Results saved to Apify key-value store")
