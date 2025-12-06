# chat.py
import os
from groq import Groq
from vector import retrieve_top_k
from dotenv import load_dotenv
load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("⚠ WARNING: GROQ_API_KEY not set; Groq calls will fail unless you set the env var.")

client = Groq(api_key=GROQ_API_KEY)

def rag_answer(query):
    
    job_results, resume_results = retrieve_top_k(query, k_jobs=5, k_resume=5)

    context = ""
    for jr in job_results:
        context += f"\n[JOB] (score={jr['score']:.3f})\n{jr['text']}\n"
    for rr in resume_results:
        context += f"\n[RESUME] (score={rr['score']:.3f})\n{rr['text']}\n"

    prompt = f"""
You are a senior software engineer and recruiter.

Use the following context to answer the question. Cite relevant context blocks when useful.

Context:
{context}

Question: {query}

Answer as clearly and practically as possible.
"""

    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
