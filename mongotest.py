# # from pymongo import MongoClient

# # client = MongoClient("mongodb://localhost:27017/")
# # db = client["testdb"]
# # collection = db["users"]

# # result = collection.insert_one({"name": "Arghya"})
# # print("Inserted:", result.inserted_id)

# # for user in collection.find():
# #     print(user)


# from vector import build_vector_db

# scraped_jobs = [
#     {
#         "title": "Backend Engineer",
#         "company": "Netflix",
#         "location": "Remote",
#         "salary": "20 LPA",
#         "description": "Looking for Python, FastAPI, SQL, Docker.",
#         "link": "https://netflix.com/job1"
#     }
# ]

# build_vector_db(scraped_jobs, pdf_path="resume.pdf")


from pymongo import MongoClient
db = MongoClient("mongodb://localhost:27017")["yourdbname"]
print(db.jobs.count_documents({}))
print(db.jobs.distinct("owner"))
