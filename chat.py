import os
from groq import Groq
from dotenv import load_dotenv
from vector import retrieve_top_k

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("⚠ WARNING: GROQ_API_KEY not set; Groq calls will fail unless you set the env var.")

client = Groq(api_key=GROQ_API_KEY)


def rag_answer(query: str):
    """
    Performs RAG:
    1. Retrieves top job + resume chunks
    2. Assembles context
    3. Queries Groq LLM
    """
    
    job_results, resume_results = retrieve_top_k(query, k_jobs=5, k_resume=5)

    if not job_results and not resume_results:
        context = "No relevant job or resume data found in vector database."
    else:
        context = ""
        for jr in job_results:
            context += f"\n[JOB] (score={jr['score']:.3f})\n{jr['text']}\n"

        for rr in resume_results:
            context += f"\n[RESUME] (score={rr['score']:.3f})\n{rr['text']}\n"


    print("\n===== RAG CONTEXT =====")
    print(context)
    print("========================\n")



    system_prompt = """
You are a senior software engineer and technical recruiter.
Use ONLY the provided context to answer questions.
If context is insufficient, say so honestly.
Give clear and practical answers.
"""

    user_prompt = f"""
Context:
{context}

User Question:
{query}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    return response.choices[0].message.content if response and response.choices else "No response from model."
