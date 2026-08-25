"""
retriever.py — Retrieval engine that embeds user queries and fetches the most
relevant corpus chunks from the ChromaDB vector store.
"""
import os
import chromadb
from chromadb.utils import embedding_functions

# Initialize globally to avoid multi-second cold starts on every request
_persist_dir = "embeddings/chroma_db"
_client = chromadb.PersistentClient(path=_persist_dir)

# Use the default ONNX embedding function instead of heavy PyTorch SentenceTransformers
# This drastically reduces RAM usage and prevents Railway container from hitting swap memory.
_emb_fn = embedding_functions.DefaultEmbeddingFunction()

try:
    _collection = _client.get_collection(name="ppfas_faq", embedding_function=_emb_fn)
except Exception:
    _collection = None


def retrieve_chunks(query: str, top_k: int = 3) -> list[dict]:
    if _collection is None:
        return []
        
    results = _collection.query(
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
