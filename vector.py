import os
import json
import numpy as np
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import requests
from io import BytesIO

# ======================================================
# CONFIG
# ======================================================
DATA_DIR = Path("./vector_data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

JOBS_JSON = DATA_DIR / "jobs_docs.json"
JOBS_EMB = DATA_DIR / "jobs_embs.npy"

RESUME_JSON = DATA_DIR / "resume_docs.json"
RESUME_EMB = DATA_DIR / "resume_embs.npy"


_embedding_model = None

def get_embedding_model():
    """
    Lazy-load the embedding model ONLY when needed.
    Prevents Render OOM crash on startup.
    """
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


# ======================================================
# TEXT SPLITTER
# ======================================================
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150
)

# ======================================================
# SAVE / LOAD HELPERS
# ======================================================
def save_json(path: Path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def load_json(path: Path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ======================================================
# USE LAZY MODEL IN EMBEDDING
# ======================================================
def embed_texts(texts, batch_size=64):
    model = get_embedding_model()   #  lazy load here
    embs = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        arr = model.encode(batch, show_progress_bar=False)
        for e in arr:
            embs.append(e.tolist())

    return embs

# ======================================================
# STORE SCRAPED JOBS
# ======================================================
def store_jobs(scraped_jobs, user_id: str):
    docs = []
    metas = []

    for idx, job in enumerate(scraped_jobs):
        content = (
            f"Job Title: {job.get('title','')}\n"
            f"Company: {job.get('company','')}\n"
            f"Location: {job.get('location','')}\n"
            f"Salary: {job.get('salary','')}\n"
            f"Description: {job.get('description','')}\n"
            f"Apply Link: {job.get('link','')}\n"
        )

        chunks = text_splitter.split_text(content)
        for c in chunks:
            docs.append(c)
            metas.append({
                "type": "job",
                "job_index": idx,
                "source": job.get("link", ""),
                "user_id": user_id
            })

    if not docs:
        print("WARNING: No job chunks to store.")
        return

    embs = embed_texts(docs)

    save_json(JOBS_JSON, [{"doc": d, "meta": m} for d, m in zip(docs, metas)])
    np.save(JOBS_EMB, np.array(embs, dtype=np.float32))

    print(f"Stored {len(docs)} job chunks.")

# ======================================================
# STORE RESUME
# ======================================================
def store_resume(pdf_source: str, user_id: str):
    try:
        if pdf_source.startswith("http"):
            resp = requests.get(pdf_source, timeout=10)
            resp.raise_for_status()
            reader = PdfReader(BytesIO(resp.content))
        else:
            if not os.path.isfile(pdf_source):
                print("Resume not found:", pdf_source)
                return
            reader = PdfReader(pdf_source)
    except Exception as e:
        print("Failed to read PDF:", e)
        return

    pages_text = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception:
            pages_text.append("")

    full_text = "\n".join(pages_text).strip()
    if not full_text:
        print("No text extracted from resume.")
        return

    chunks = text_splitter.split_text(full_text)
    embeddings = embed_texts(chunks)

    save_json(
        RESUME_JSON,
        [{"doc": c, "meta": {"type": "resume", "chunk_index": i, "user_id": user_id}}
         for i, c in enumerate(chunks)]
    )

    np.save(RESUME_EMB, np.array(embeddings, dtype=np.float32))
    print(f"Stored {len(chunks)} resume chunks.")

# ======================================================
# SAFE LOAD STORE (NO MODEL AT IMPORT)
# ======================================================
def _load_store(json_path, emb_path):
    items = load_json(json_path)

    if not items or not Path(emb_path).exists():
        model = get_embedding_model() 
        return [], np.zeros(
            (0, model.get_sentence_embedding_dimension()),
            dtype=np.float32
        ), []

    embs = np.load(emb_path)
    docs = [it["doc"] for it in items]
    metas = [it["meta"] for it in items]

    return docs, embs, metas

# ======================================================
# COSINE SIMILARITY
# ======================================================
def _cosine_similarities(query_emb, emb_matrix):
    if emb_matrix.size == 0:
        return np.array([])

    q = query_emb / np.linalg.norm(query_emb)
    M = emb_matrix / np.linalg.norm(emb_matrix, axis=1, keepdims=True)
    return (M @ q).astype(np.float32)

# ======================================================
# LAZY MODEL IN RETRIEVAL
# ======================================================
def retrieve_top_k(query, user_id: str, k_jobs=5, k_resume=5):
    model = get_embedding_model()   #  lazy load here
    q_emb = model.encode([query])[0].astype(np.float32)

    job_docs, job_embs, job_meta = _load_store(JOBS_JSON, JOBS_EMB)
    job_sims = _cosine_similarities(q_emb, job_embs)

    job_results = []
    if job_sims.size:
        for i in np.argsort(-job_sims):
            if job_meta[i].get("user_id") != user_id:
                continue
            job_results.append({
                "text": job_docs[i],
                "score": float(job_sims[i]),
                "meta": job_meta[i]
            })
            if len(job_results) == k_jobs:
                break


    resume_docs, resume_embs, resume_meta = _load_store(RESUME_JSON, RESUME_EMB)
    resume_sims = _cosine_similarities(q_emb, resume_embs)

    resume_results = []
    if resume_sims.size:
        for i in np.argsort(-resume_sims):
            if resume_meta[i].get("user_id") != user_id:
                continue
            resume_results.append({
                "text": resume_docs[i],
                "score": float(resume_sims[i]),
                "meta": resume_meta[i]
            })
            if len(resume_results) == k_resume:
                break


    return job_results, resume_results


