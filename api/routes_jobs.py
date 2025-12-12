from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from pathlib import Path
import shutil

from api.db import users_col, jobs_col
from api.deps import get_current_user

from scrape import scrape_indeed
from scrape_naukri import scrape_naukri
from vector import store_jobs
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
from api.imagekit_client import imagekit
import os

router = APIRouter(prefix="/api", tags=["jobs"])


RESUME_DIR = Path("./resumes")
RESUME_DIR.mkdir(exist_ok=True)


# # ---------------- UPLOAD RESUME ------------------
# @router.post("/upload_resume")
# async def upload_resume(
#     file: UploadFile = File(...),
#     current_user: dict = Depends(get_current_user)
# ):
#     user_id = current_user["sub"]

#     if file.content_type not in ("application/pdf",):
#         raise HTTPException(400, "Only PDF resumes supported.")

#     dest = RESUME_DIR / f"{user_id}.pdf"

#     with open(dest, "wb") as f:
#         shutil.copyfileobj(file.file, f)

#     from vector import store_resume  
#     store_resume(str(dest))

#     users_col.update_one(
#         {"_id": __import__("bson").ObjectId(user_id)},
#         {"$set": {"resume_path": str(dest)}},
#     )

#     return {"status": "ok", "path": str(dest)}

@router.post("/upload_resume")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    import bson, base64
    from api.imagekit_client import imagekit

    # ImageKit object for options
    class UploadOptions:
        def __init__(self, folder, use_unique_file_name, is_private_file):
            self.folder = folder
            self.use_unique_file_name = use_unique_file_name
            self.is_private_file = is_private_file

    user_id = current_user["sub"]

    # Validate PDF
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty PDF")

    # Convert PDF to base64
    pdf_base64 = base64.b64encode(pdf_bytes).decode()

    # Fetch existing user
    user = users_col.find_one({"_id": bson.ObjectId(user_id)})
    old_file_id = user.get("resume_file_id")

    # Delete previous resume if exists
    if old_file_id:
        try:
            imagekit.delete_file(file_id=old_file_id)
        except Exception as e:
            print("Error deleting old resume:", e)

    # Upload options
    options = UploadOptions(
        folder="/resumes/",
        use_unique_file_name=True,
        is_private_file=False
    )

    # Upload to ImageKit (base64)
    try:
        print("Uploading PDF using base64...")

        upload_response = imagekit.upload_file(
            file=pdf_base64,
            file_name=f"{user_id}_resume.pdf",
            options=options
        )

        print("ImageKit Response:", upload_response)

    except Exception as e:
        import traceback
        print("ImageKit ERROR:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"ImageKit error: {str(e)}")

    # get URL
    resume_url = upload_response.url
    print (resume_url)
    resume_file_id = upload_response.file_id

    # Save PDF metadata to Mongodb
    users_col.update_one(
        {"_id": bson.ObjectId(user_id)},
        {
            "$set": {
                "resume_url": resume_url,
                "resume_file_id": resume_file_id
            }
        }
    )



    # Store embeddings to vector db
    from vector import store_resume
    store_resume(resume_url)

    return {
        "status": "ok",
        "resume_url": resume_url,
        "message": "Resume uploaded successfully"
    }



# ------------------ SCRAPE & STORE ----------------
@router.post("/scrape")
def trigger_scrape(
    job_title: str = Form(...),
    location: str = Form(""),
    pages: int = Form(1),
    current_user: dict = Depends(get_current_user)
):
    scraped_naukri = scrape_naukri(job_title.replace(" ", "+"), location, max_pages=int(pages))
    scraped_indeed = scrape_indeed(job_title.replace(" ", "+"), location, max_pages=int(pages))

    scraped = scraped_naukri + scraped_indeed
    
    for s in scraped:
        s["owner"] = current_user["sub"]

    if scraped:
        jobs_col.delete_many({"owner": current_user["sub"]})
        jobs_col.insert_many(scraped)
        store_jobs(scraped)

    return {
        "count": len(scraped),
        "naukri": len(scraped_naukri),
        "indeed": len(scraped_indeed)
        }


# ------------------ GET SCRAPED JOBS --------------------
@router.get("/jobs")
def get_jobs(current_user: dict = Depends(get_current_user)):
    user_id = current_user["sub"]

    jobs = list(jobs_col.find({"owner": user_id}))

    
    for j in jobs:
        j["_id"] = str(j["_id"])

    return {"jobs": jobs}
