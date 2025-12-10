# RAG Chatbot for finding jobs

A lightweight RAG-based chatbot that:

- Scrapes job listings from Indeed
- Embeds resume + job descriptions into a vector database
- Matches the best jobs for a candidate
- Provides conversational insights using Groq LLMs

---

## ✨ Features

### 🔐 Authentication

- User Registration & Login
- JWT-based authentication
- Secure password hashing
- Protected endpoints

### 🧠 AI-Driven Job Matching

- Resume uploaded → automatically extracted, chunked & embedded
- Scraped jobs → chunked & embedded
- ChromaDB stores all embeddings for similarity search
- LLM chatbot evaluates:
  - Job–resume match score
  - Missing skills
  - Fit analysis across all scraped jobs

### 🕸️ Web Scraping (Indeed)

- Automated job scraping using:
  - BeautifulSoup
  - Selenium + WebDriver Manager
- Extracts:
  - Title
  - Company
  - Location
  - Full job description
  - Apply link

### 📄 Resume Processing

- Accepts PDF uploads
- Text extraction using:
  - PyMuPDF
  - PyPDF
- Automatic preprocessing + splitting
- Vector embedding with Sentence Transformers

### 🗄️ Database

MongoDB stores:

- User accounts
- User resumes
- Scraped jobs (full descriptions, links, metadata)

ChromaDB stores:

- Embeddings for jobs
- Embeddings for resumes
- Used for similarity search during AI analysis

### 💬 Chatbot

- Powered by LLM via Groq API
- Answers smart queries like:
  - _“Which of the newly scraped jobs are best for me?”_
  - _“What should I improve in my resume?”_
  - _“Compare my resume to the job requirements.”_

### 🖥️ UI

- Upload resume
- View upload success state
- View scraped jobs
- Click to open full job description in modal
- Chat interface for job-matching queries

---

## ⚙️ Tech Stack

- **FastAPI** – Backend web framework
- **Python** – Core backend language
- **OAuth2 + JWT Auth** – Secure authentication (OAuth2PasswordBearer with JWT tokens)
- **MongoDB (PyMongo)** – Database for users, resumes & scraped jobs
- **ChromaDB** – Vector database for semantic search
- **Sentence Transformers** – Embedding model for resume + job descriptions
- **LangChain Text Splitters** – Chunking for RAG pipeline
- **PyMuPDF & PyPDF** – Resume text extraction
- **Selenium + BeautifulSoup** – Job scraping from Indeed
- **Groq LLM API** – Fast LLM inference for chatbot responses
- **Uvicorn** – ASGI server
- **Docker & Docker Compose** – Containerized deployment (future)

---

## 🚀 How to Run

### 1️⃣ Clone the repository

```bash
git clone <repo-url>
cd RAG-Job-Finder-Chatbot
```

### 2️⃣ Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Linux / Mac
.venv\Scripts\activate         # Windows
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Set up environment variables

Set up your environment varialbles in `.env` as in `env_example.txt`

### 5️⃣ Run the server

```bash
uvicorn app.main:app --reload
```

Visit:  
👉 **http://127.0.0.1:8000**

---

## 🧪 Example Usage

### ✔ Register User

**POST** `/register`

### ✔ Login User

**POST** `/login`  
Returns JWT token.

### ✔ Scrape Jobs

**POST** `/scrape-jobs`  
Scrapes from Indeed and stores full job data.

### ✔ Upload Resume

**POST** `/upload-resume`  
Stores + embeds resume in ChromaDB.

### ✔ Get All Jobs

**GET** `/jobs`

### ✔ AI Chat

**POST** `/chat`  
Send query → get intelligent job-matching response.

---

## 👤 Author

**Arghya Malakar**  
📧 arghyaapply2016@gmail.com  
🌐 GitHub: https://github.com/hunterarghya
