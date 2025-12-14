import os
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
import requests
from io import BytesIO

# ---------------- CONFIG ---------------------
DATA_DIR = Path("./vector_data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

JOBS_JSON = DATA_DIR / "jobs_docs.json"
JOBS_EMB = DATA_DIR / "jobs_embs.npy"

RESUME_JSON = DATA_DIR / "resume_docs.json"
RESUME_EMB = DATA_DIR / "resume_embs.npy"

# -------------- Embedding model ----------------------
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

def embed_texts(texts, batch_size=64):
    """Return list-of-lists embeddings for given list of texts."""
    embs = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        arr = embedding_model.encode(batch, show_progress_bar=False)
        for e in arr:
            e = e.tolist() if hasattr(e, "tolist") else list(e)
            embs.append(e)
    return embs

# ----------------- Text splitter -----------------------
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150
)

# ----------- save/load --------------------
def save_json(path: Path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def load_json(path: Path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ------------ STORE SCRAPED JOBS ---------------------------------------------------------------
def store_jobs(scraped_jobs):
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
                "source": job.get("link", "")
            })

    if not docs:
        print("WARNING!!! No job chunks to store.")
        return

    embs = embed_texts(docs)
    save_json(JOBS_JSON, [{"doc": d, "meta": m} for d, m in zip(docs, metas)])
    np.save(JOBS_EMB, np.array(embs, dtype=np.float32))

    print(f"BINGO!!!! Stored {len(docs)} job chunks.")

# --------- STORE RESUME PDF ---------------------------------------
# def store_resume(pdf_path="./resume.pdf"):
#     if not os.path.exists(pdf_path):
#         print("WARNING!!! Resume PDF not found at", pdf_path)
#         return

#     try:
#         reader = PdfReader(pdf_path)
#         pages = []
#         for p in reader.pages:
#             try:
#                 pages.append(p.extract_text() or "")
#             except Exception:
#                 pages.append("")
#         full_text = "\n".join(pages).strip()
#     except Exception as e:
#         print("WARNING!!! Error reading PDF:", e)
#         return

#     if not full_text:
#         print("WARNING!!!! No text extracted from resume.")
#         return

#     chunks = text_splitter.split_text(full_text)
#     embs = embed_texts(chunks)

#     save_json(
#         RESUME_JSON,
#         [{"doc": c, "meta": {"type": "resume", "chunk_index": i}} for i, c in enumerate(chunks)]
#     )
#     np.save(RESUME_EMB, np.array(embs, dtype=np.float32))

#     print(f"BINGO!!! Stored {len(chunks)} resume chunks.")

# store resume- imagekit version
def store_resume(pdf_source: str):
    """
    pdf_source:
    - URL from ImageKit
    - or local file path
    """

    
    import requests
    from io import BytesIO
    import numpy as np
    import os

    # READ PDF ----------------
    try:
        if pdf_source.startswith("http"):
            # Remote PDF
            resp = requests.get(pdf_source, timeout=10)
            resp.raise_for_status()

            reader = PdfReader(BytesIO(resp.content))
        else:
            # Local file path
            if not os.path.isfile(pdf_source):
                print("Resume not found at:", pdf_source)
                return

            reader = PdfReader(pdf_source)

    except Exception as e:
        print("Failed to read PDF:", e)
        return

    #  EXTRACT TEXT 
    pages_text = []
    for page in reader.pages:
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        pages_text.append(txt)

    full_text = "\n".join(pages_text).strip()

    if not full_text:
        print("No text extracted from PDF.")
        return

    # EMBEDDINGS 
    chunks = text_splitter.split_text(full_text)
    embeddings = embed_texts(chunks)

    save_json(
        RESUME_JSON,
        [{"doc": c, "meta": {"type": "resume", "chunk_index": i}} for i, c in enumerate(chunks)]
    )

    np.save(RESUME_EMB, np.array(embeddings, dtype=np.float32))

    print(f"Stored {len(chunks)} resume chunks successfully.")



# --------- retrieval (cosine) ---------------------------------------------
def _load_store(json_path, emb_path):
    items = load_json(json_path)
    if not items or not Path(emb_path).exists():
        return [], np.zeros((0, embedding_model.get_sentence_embedding_dimension()), dtype=np.float32), []

    embs = np.load(emb_path)
    docs = [it["doc"] for it in items]
    metas = [it["meta"] for it in items]
    return docs, embs, metas

def _cosine_similarities(query_emb, emb_matrix):
    if emb_matrix.size == 0:
        return np.array([])

    q = query_emb / np.linalg.norm(query_emb)
    M = emb_matrix / np.linalg.norm(emb_matrix, axis=1, keepdims=True)
    return (M @ q).astype(np.float32)

def retrieve_top_k(query, k_jobs=5, k_resume=5):
    q_emb = embedding_model.encode([query])[0].astype(np.float32)

    # -------- jobs --------
    job_docs, job_embs, job_meta = _load_store(JOBS_JSON, JOBS_EMB)
    job_sims = _cosine_similarities(q_emb, job_embs)
    job_results = []
    if job_sims.size:
        top = np.argsort(-job_sims)[:k_jobs]
        for i in top:
            job_results.append({"text": job_docs[i], "score": float(job_sims[i]), "meta": job_meta[i]})

    # ------ resume --------
    resume_docs, resume_embs, resume_meta = _load_store(RESUME_JSON, RESUME_EMB)
    resume_sims = _cosine_similarities(q_emb, resume_embs)
    resume_results = []
    if resume_sims.size:
        top = np.argsort(-resume_sims)[:k_resume]
        for i in top:
            resume_results.append({"text": resume_docs[i], "score": float(resume_sims[i]), "meta": resume_meta[i]})

    return job_results, resume_results


def build_vector_db(scraped_jobs, pdf_path="./resume.pdf"):
    store_jobs(scraped_jobs)
    store_resume(pdf_path)
    print("BINGO!!! Vector DB built successfully.")
