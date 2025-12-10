# # main.py

# from scrape import scrape_indeed

# if __name__ == "__main__":
#     job = "software+developer"
#     location = "Kolkata"

#     results = scrape_indeed(job, location, max_pages=3)

#     print("\n--- SCRAPED RESULTS ---\n")
#     for r in results:
        
        
#         print(f"Job Title: {r['title']}")
#         print(f"Company: {r['company']}")
#         print(f"Location: {r['location']}")
#         print(f"Salary: {r['salary']}")
#         print(f"Description: {r['description']}")
#         print(f"Apply Link: {r['link']}")
#         print("-" * 40)

#     print(f"\nTotal jobs scraped: {len(results)}")




from scrape import scrape_indeed
from vector import build_vector_db
from chat import rag_answer

if __name__ == "__main__":
    # SCRAPE
    print("Scraping Indeed...")
    scraped_jobs = scrape_indeed("software+developer", "Kolkata", max_pages=2)

    print(f"Scraped {len(scraped_jobs)} jobs.")

    # VECTOR DB
    print("Building vector database...")
    build_vector_db(scraped_jobs)

    # CHATBOT LOOP
    print("\nRAG Chatbot ready! Ask anything. Press q to quit.\n")

    while True:
        query = input("You: ")
        if query.lower() == "q":
            break

        answer = rag_answer(query)
        print("\nBot:", answer, "\n")
