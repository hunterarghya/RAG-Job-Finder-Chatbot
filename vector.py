# vector.py
import os
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

# ------------------ CONFIG ---------------------
DATA_DIR = Path("./vector_data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

JOBS_JSON = DATA_DIR / "jobs_docs.json"
JOBS_EMB = DATA_DIR / "jobs_embs.npy"

RESUME_JSON = DATA_DIR / "resume_docs.json"
RESUME_EMB = DATA_DIR / "resume_embs.npy"

# ---------------- Embedding model (local) ----------------------
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

def embed_texts(texts, batch_size=64):
    """Return list-of-lists embeddings for given list of texts."""
    embs = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        arr = embedding_model.encode(batch, show_progress_bar=False)
        embs.extend([e.tolist() if hasattr(e, "tolist") else list(e) for e in arr])
    return embs

# -------------------- Text splitter -----------------------
text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)

# ----------- Helper save/load --------------------
def save_json(path: Path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def load_json(path: Path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ------------ 1) STORE SCRAPED JOBS ---------------------------------------------------------------
def store_jobs(scraped_jobs):
    """
    scraped_jobs: list of dicts with keys:
      title, company, location, salary, description, link
    Stores chunked job texts + embeddings to files.
    """
    docs = []
    metadatas = []
    for idx, job in enumerate(scraped_jobs):
        content = (
            f"Job Title: {job.get('title','')}\n"
            f"Company: {job.get('company','')}\n"
            f"Location: {job.get('location','')}\n"
            f"Salary: {job.get('salary','')}\n"
            f"Description: {job.get('description','')}\n"
            f"Apply Link: {job.get('link','')}"
        )
        chunks = text_splitter.split_text(content)
        for c_i, chunk in enumerate(chunks):
            docs.append(chunk)
            metadatas.append({"type": "job", "job_index": idx, "source": job.get("link","")})

    if not docs:
        print("No job chunks to store.")
        return

    embs = embed_texts(docs)
    # persist
    save_json(JOBS_JSON, [{"doc": d, "meta": m} for d,m in zip(docs, metadatas)])
    np.save(JOBS_EMB, np.array(embs, dtype=np.float32))
    print(f"Stored {len(docs)} job chunks (files under {DATA_DIR})")

# --------- 2) STORE RESUME PDF ---------------------------------------
def store_resume(pdf_path="./resume.pdf"):
    if not os.path.exists(pdf_path):
        print("Resume not found at", pdf_path)
        return

    try:
        reader = PdfReader(pdf_path)
        pages = []
        for p in reader.pages:
            try:
                pages.append(p.extract_text() or "")
            except Exception:
                pages.append("")
        full_text = "\n".join(pages).strip()
    except Exception as e:
        print("Error reading PDF:", e)
        return

    if not full_text:
        print("No text extracted from resume.")
        return

    chunks = text_splitter.split_text(full_text)
    embs = embed_texts(chunks)

    save_json(RESUME_JSON, [{"doc": c, "meta": {"type":"resume","source":pdf_path,"chunk_index":i}} for i,c in enumerate(chunks)])
    np.save(RESUME_EMB, np.array(embs, dtype=np.float32))
    print(f"Stored {len(chunks)} resume chunks (files under {DATA_DIR})")

# --------- retrieval (cosine) ---------------------------------------------
def _load_store(json_path, emb_path):
    items = load_json(json_path)
    if not items or not Path(emb_path).exists():
        return [], np.zeros((0, embedding_model.get_sentence_embedding_dimension()), dtype=np.float32)
    embs = np.load(emb_path)
    docs = [it["doc"] for it in items]
    metas = [it["meta"] for it in items]
    return docs, embs, metas

def _cosine_similarities(query_emb, emb_matrix):
    # query_emb: (d,), emb_matrix: (n,d)
    if emb_matrix.size == 0:
        return np.array([])
    q = query_emb / np.linalg.norm(query_emb)
    M = emb_matrix / np.linalg.norm(emb_matrix, axis=1, keepdims=True)
    sims = (M @ q).astype(np.float32)
    return sims

def retrieve_top_k(query, k_jobs=5, k_resume=5):
    """
    Returns (top_job_texts, top_resume_texts)
    """
    # compute query embedding
    q_emb = embedding_model.encode([query])[0].astype(np.float32)

    # jobs
    job_docs, job_embs, job_metas = _load_store(JOBS_JSON, JOBS_EMB)
    job_sims = _cosine_similarities(q_emb, job_embs)
    job_results = []
    if job_sims.size:
        top_idx = np.argsort(-job_sims)[:k_jobs]
        for i in top_idx:
            job_results.append({"text": job_docs[i], "score": float(job_sims[i]), "meta": job_metas[i]})

    # resume
    resume_docs, resume_embs, resume_metas = _load_store(RESUME_JSON, RESUME_EMB)
    resume_sims = _cosine_similarities(q_emb, resume_embs)
    resume_results = []
    if resume_sims.size:
        top_idx = np.argsort(-resume_sims)[:k_resume]
        for i in top_idx:
            resume_results.append({"text": resume_docs[i], "score": float(resume_sims[i]), "meta": resume_metas[i]})

    return job_results, resume_results


def build_vector_db(scraped_jobs, pdf_path="./resume.pdf"):
    
    store_jobs(scraped_jobs)
    store_resume(pdf_path)
