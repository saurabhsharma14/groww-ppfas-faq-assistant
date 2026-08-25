"""
retriever.py — Retrieval engine that embeds user queries and fetches the most
relevant corpus chunks from the ChromaDB vector store.
"""
import os
import chromadb
from chromadb.utils import embedding_functions

def retrieve_chunks(query: str, top_k: int = 3) -> list[dict]:
    # Use environment variable or default path relative to the app
    persist_dir = os.environ.get("CHROMA_PERSIST_DIR", "embeddings/chroma_db")
    client = chromadb.PersistentClient(path=persist_dir)
    
    model_name = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
    
    try:
        collection = client.get_collection(name="ppfas_faq", embedding_function=emb_fn)
    except Exception:
        # Collection might not exist yet
        return []
        
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )
    
    chunks = []
    if results and results.get('documents') and len(results['documents']) > 0:
        # Avoid indexing out of bounds if result is empty
        for i in range(len(results['documents'][0])):
            doc = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            chunks.append({
                "content": doc,
                "metadata": meta
            })
            
    return chunks
