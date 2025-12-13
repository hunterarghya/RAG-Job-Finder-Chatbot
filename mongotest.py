from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGO_URI")
client = MongoClient(uri)


MONGO_DB = os.getenv("MONGO_DB", "aiproj_db")

db = client[MONGO_DB]

# db.users.insert_one({"_init": True})
# db.jobs.insert_one({"_init": True})

# print("Database and collections initialized")

# print(client.list_database_names())
