"""
main.py — FastAPI application entry point for the PPFAS FAQ Assistant.
"""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.query_guard import classify_query, QueryType
from backend.retriever import retrieve_chunks
from backend.llm import generate_answer
from backend.refusal_handler import get_refusal_message

app = FastAPI(title="PPFAS FAQ Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    query: str

class AskResponse(BaseModel):
    answer: str
    source_url: str
    last_updated: str
    is_refusal: bool

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    qtype = classify_query(request.query)
    
    if qtype != QueryType.FACTUAL:
        refusal_msg = get_refusal_message(qtype)
        return AskResponse(
            answer=refusal_msg,
            source_url="https://groww.in/mutual-funds/category/ppfas-mutual-fund",
            last_updated="",
            is_refusal=True
        )
        
    # Normalize query for better retrieval matching since the fund was scraped as "Long Term Value Fund"
    search_query = request.query.replace("Flexi Cap", "Long Term Value")
    search_query = search_query.replace("flexi cap", "long term value")
    search_query = search_query.replace("Flexi cap", "Long term value")
    
    chunks = retrieve_chunks(search_query)
    
    if not chunks:
        return AskResponse(
            answer="I don't have this information. Please visit: https://groww.in/mutual-funds/category/ppfas-mutual-fund",
            source_url="https://groww.in/mutual-funds/category/ppfas-mutual-fund",
            last_updated="",
            is_refusal=False
        )
        
    llm_res = generate_answer(request.query, chunks)
    
    return AskResponse(
        answer=llm_res["answer"],
        source_url=llm_res["source_url"],
        last_updated=llm_res["last_updated"],
        is_refusal=False
    )

@app.get("/status")
async def status():
    persist_dir = "embeddings/chroma_db"
    import chromadb
    try:
        client = chromadb.PersistentClient(path=persist_dir)
        # Using get_collection assuming it is already populated
        collection = client.get_collection(name="ppfas_faq")
        count = collection.count()
        return {"status": "ok", "corpus_size": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}
