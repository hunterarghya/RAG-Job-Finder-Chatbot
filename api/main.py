from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.routes_auth import router as auth_router
from api.routes_jobs import router as jobs_router
from api.routes_chat import router as chat_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

app = FastAPI(title="AIPROJ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(chat_router)

# serve frontend
app.mount("/static", StaticFiles(directory="api/static"), name="static")


# Serve index.html on root
@app.get("/")
def serve_home():
    return FileResponse(os.path.join("api", "static", "index.html"))