import asyncio
import logging
import sys
from scraper.scrape import scrape_all, validate_chunks
from embeddings.ingest import main as ingest_main

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("ingest_pipeline")

def run_pipeline():
    log.info("Starting ingestion pipeline...")
    
    log.info("Step 1: Scraping data from Groww...")
    try:
        asyncio.run(scrape_all())
    except Exception as e:
        log.error(f"Scraping failed: {e}")
        sys.exit(1)
        
    log.info("Step 2: Validating chunks...")
    is_valid = validate_chunks()
    if not is_valid:
        log.warning("Validation failed for some chunks. Proceeding with ingestion of valid data only.")

    log.info("Step 3: Generating embeddings and updating ChromaDB...")
    try:
        ingest_main()
    except Exception as e:
        log.error(f"Embedding/Ingestion failed: {e}")
        sys.exit(1)
    
    log.info("Ingestion pipeline completed successfully.")

if __name__ == "__main__":
    run_pipeline()
