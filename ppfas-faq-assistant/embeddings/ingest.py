import json
import logging
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("ingest")

CORPUS_DIR = Path("corpus/chunks")
DB_DIR = Path("embeddings/chroma_db")


def format_field_name(field: str) -> str:
    """Convert snake_case to Title Case. e.g., expense_ratio -> Expense Ratio"""
    return field.replace("_", " ").title()


def get_text_to_embed(chunk_data: dict) -> str:
    """Format the chunk into a semantic string for embedding."""
    scheme = chunk_data["scheme_name"]
    field = format_field_name(chunk_data["field"])
    value = chunk_data["value"]
    
    # Example: "Parag Parikh Long Term Value Fund — Expense Ratio: 0.68%"
    return f"{scheme} — {field}: {value}"


def main():
    if not CORPUS_DIR.exists():
        log.error(f"Corpus directory not found: {CORPUS_DIR}")
        return

    # 1. Setup ChromaDB client and collection
    client = chromadb.PersistentClient(path=str(DB_DIR))
    
    # We use the recommended local sentence-transformer (fast, free, no API key)
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    
    collection = client.get_or_create_collection(
        name="ppfas_faq",
        embedding_function=emb_fn,
        metadata={"description": "Facts extracted from Groww PPFAS mutual fund pages"}
    )
    
    # 2. Read chunks and prepare data
    documents = []
    metadatas = []
    ids = []
    
    json_files = list(CORPUS_DIR.glob("*.json"))
    # Filter out the scrape summary file
    json_files = [f for f in json_files if f.name != "scrape_summary.json"]
    
    log.info(f"Found {len(json_files)} chunk files to ingest.")
    
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            text = get_text_to_embed(data)
            
            # Create a deterministic ID from the filename (e.g. slug__field)
            doc_id = file_path.stem 
            
            metadata = {
                "scheme_name": data.get("scheme_name", ""),
                "field": data.get("field", ""),
                "source_url": data.get("source_url", ""),
                "last_scraped_at": data.get("last_scraped_at", "")
            }
            
            documents.append(text)
            metadatas.append(metadata)
            ids.append(doc_id)
            
        except Exception as e:
            log.error(f"Error reading {file_path.name}: {e}")
            
    # 3. Add to ChromaDB
    if ids:
        log.info("Generating embeddings and upserting into ChromaDB... (This may take a moment to download the model on the first run)")
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        log.info(f"Successfully ingested {len(ids)} facts into collection '{collection.name}'.")
    else:
        log.warning("No data found to ingest.")
        
    # 4. Quick validation
    count = collection.count()
    log.info(f"Vector store now contains {count} items.")
    
    log.info("\n─── Running Validation Search ───")
    query = "What is the exit load for ELSS?"
    log.info(f"Query: '{query}'")
    
    results = collection.query(
        query_texts=[query],
        n_results=3
    )
    
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        score = results['distances'][0][i]
        log.info(f"Result {i+1} (distance={score:.4f}): {doc}")


if __name__ == "__main__":
    main()
