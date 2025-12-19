import json
import numpy as np
from pathlib import Path

# ======================================================
# CONFIG (match vector.py exactly)
# ======================================================
DATA_DIR = Path("./vector_data")

JOBS_JSON = DATA_DIR / "jobs_docs.json"
JOBS_EMB = DATA_DIR / "jobs_embs.npy"

RESUME_JSON = DATA_DIR / "resume_docs.json"
RESUME_EMB = DATA_DIR / "resume_embs.npy"


# ======================================================
# LOAD HELPERS
# ======================================================
def _load_json(path: Path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _cosine_sim_matrix(A: np.ndarray, B: np.ndarray):
    """
    A: (n_resume_chunks, dim)
    B: (n_job_chunks, dim)
    Returns: (n_resume_chunks, n_job_chunks)
    """
    if A.size == 0 or B.size == 0:
        return np.zeros((0, 0), dtype=np.float32)

    A_norm = A / np.linalg.norm(A, axis=1, keepdims=True)
    B_norm = B / np.linalg.norm(B, axis=1, keepdims=True)

    return (A_norm @ B_norm.T).astype(np.float32)


# ======================================================
# MAIN SIMILARITY FUNCTION
# ======================================================
def compute_job_resume_matches(user_id: str, threshold: float = 0.6):
    """
    Returns:
        List of dicts:
        [
            {
                "job_index": int,
                "score": float
            }
        ]
    """

    # -------- Load stored data --------
    if not JOBS_EMB.exists() or not RESUME_EMB.exists():
        return []

    jobs_items = _load_json(JOBS_JSON)
    resume_items = _load_json(RESUME_JSON)

    job_embs = np.load(JOBS_EMB)
    resume_embs = np.load(RESUME_EMB)

    # -------- Filter by user_id --------
    job_indices = [
        i for i, it in enumerate(jobs_items)
        if it["meta"].get("user_id") == user_id
    ]

    resume_indices = [
        i for i, it in enumerate(resume_items)
        if it["meta"].get("user_id") == user_id
    ]

    if not job_indices or not resume_indices:
        return []

    job_vecs = job_embs[job_indices]
    resume_vecs = resume_embs[resume_indices]

    # -------- Similarity matrix --------
    sim_matrix = _cosine_sim_matrix(resume_vecs, job_vecs)


    # -------- Aggregate per job -------
    # max resume chunk similarity per job chunk
    job_chunk_scores = sim_matrix.max(axis=0)

    job_chunk_map = {}  # job_index -> best_score

    for local_idx, score in enumerate(job_chunk_scores):
        if score < threshold:
            continue

        # global index in vector store
        global_idx = job_indices[local_idx]

        # get metadata of that job chunk
        job_meta = jobs_items[global_idx]["meta"]

        # ORIGINAL job index from scraped list
        job_idx = job_meta["job_index"]

        # keep max score per job
        job_chunk_map[job_idx] = max(
            job_chunk_map.get(job_idx, 0),
            float(score)
        )

    # convert to result list
    results = [
        {"job_index": job_idx, "score": score}
        for job_idx, score in job_chunk_map.items()
    ]

    return results
