from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from pathlib import Path
import shutil

from api.db import users_col, jobs_col
from api.deps import get_current_user

from scrape import scrape_indeed
from vector import store_jobs

router = APIRouter(prefix="/api", tags=["jobs"])


RESUME_DIR = Path("./resumes")
RESUME_DIR.mkdir(exist_ok=True)


# ---------------- UPLOAD RESUME ------------------
@router.post("/upload_resume")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["sub"]

    if file.content_type not in ("application/pdf",):
        raise HTTPException(400, "Only PDF resumes supported.")

    dest = RESUME_DIR / f"{user_id}.pdf"

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    from vector import store_resume  
    store_resume(str(dest))

    users_col.update_one(
        {"_id": __import__("bson").ObjectId(user_id)},
        {"$set": {"resume_path": str(dest)}},
    )

    return {"status": "ok", "path": str(dest)}


# ------------------ SCRAPE & STORE ----------------
@router.post("/scrape")
def trigger_scrape(
    job_title: str = Form(...),
    location: str = Form(""),
    pages: int = Form(1),
    current_user: dict = Depends(get_current_user)
):
    scraped = scrape_indeed(job_title.replace(" ", "+"), location, max_pages=int(pages))

    
    for s in scraped:
        s["owner"] = current_user["sub"]

    if scraped:
        jobs_col.insert_many(scraped)
        store_jobs(scraped)

    return {"count": len(scraped)}


# ------------------ GET SCRAPED JOBS --------------------
@router.get("/jobs")
def get_jobs(current_user: dict = Depends(get_current_user)):
    user_id = current_user["sub"]

    jobs = list(jobs_col.find({"owner": user_id}))

    
    for j in jobs:
        j["_id"] = str(j["_id"])

    return {"jobs": jobs}
