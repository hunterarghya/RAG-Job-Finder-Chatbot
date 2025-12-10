from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "aiproj_db")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

users_col = db["users"]
jobs_col = db["jobs"]
