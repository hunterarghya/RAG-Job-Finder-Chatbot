import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from celery import Celery


REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

app = Celery('tasks', 
             broker=f'redis://{REDIS_HOST}:6379/0', 
             backend=f'redis://{REDIS_HOST}:6379/0')

# Configure RedBeat
app.conf.redbeat_redis_url = f"redis://{REDIS_HOST}:6379/0"
# Windows Compatibility fix
app.conf.worker_pool_restarts = True

@app.task
def scheduled_job_process(user_id, job_title, location):

    from api.db import users_col, jobs_col
    import bson
    # 1. Scrape jobs
    from scrape_naukri import scrape_naukri
    from vector import store_jobs, store_resume

    scraped = scrape_naukri(job_title.replace(" ", "+"), location, max_pages=1)

    for s in scraped:
        s["owner"] = user_id

    if scraped:
        jobs_col.delete_many({"owner": user_id})
        jobs_col.insert_many(scraped)
        store_jobs(scraped, user_id)

    user = users_col.find_one({"_id": bson.ObjectId(user_id)})

    if user.get("resume_url"):
        store_resume(user["resume_url"], user_id)



    # ------------------
    # 5. Similarity (BATCH)
    # ------------------
    from worker_similarity import compute_job_resume_matches
    matches = compute_job_resume_matches(
        user_id=user_id,
        threshold=0.6
    )

    print (matches)



    # ------------------
    # 6. Email
    # ------------------
    for match in matches:
        job = scraped[match["job_index"]]

        
        from worker_mailer import send_email_logic
        
        send_email_logic(user["email"],
                          job["title"], 
                          match['score'], 
                          job["company"], 
                          job["link"]
                    )


    return f"{len(matches)} strong matches emailed"


    
    

   

    