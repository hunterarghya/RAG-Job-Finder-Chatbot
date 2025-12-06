# Job Matcher RAG Chatbot

A lightweight RAG-based chatbot that:

- Scrapes job listings from Indeed
- Embeds resume + job descriptions into a vector database
- Matches the best jobs for a candidate
- Provides conversational insights using Groq LLMs

## Features

- Indeed job scraping (Selenium)
- Sentence-transformers vector embeddings
- ChromaDB vector store
- RAG-based job matching
- CLI chatbot for querying job fit

## Tech Stack

- Python 3.10
- Selenium + BeautifulSoup
- Sentence-Transformers
- ChromaDB
- Groq API (LLMs)
- FastAPI (coming soon)

## How to Run

```bash
python main.py
```
