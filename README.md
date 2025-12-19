# RAG Chatbot for finding jobs

A lightweight RAG-based chatbot that:

- Scrapes job listings from Indeed and Naukri
- Embeds resume + job descriptions into a vector database
- Matches the best jobs for a candidate
- Provides conversational insights using Groq LLMs
- Automatically monitors new jobs and notifies users via email when high-fit roles appear

Purpose of the Application:

A unified job-search platform that **automatically scrapes jobs from multiple portals like LinkedIn, Indeed, Naukri etc** , centralizes them in one dashboard, and uses an **AI chatbot** to **analyze your resume**, recommend the **best-fit roles** according to the skills in the resume or the user's **personal preferences**, and highlight **missing skills** or **market demands**—so you don't need to visit multiple sites or read every job description manually.
Additionally, the system can **run automated background job searches on a schedule (daily / weekly)** and proactively notify users when strong matches are found, removing the need for manual searching altogether.

🚀 **Demo:** [Watch a demo](https://drive.google.com/file/d/18omur_TgE-z8Go6iHtZmHfMKxK9SpGbB/view?usp=sharing)

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

### 🕸️ Web Scraping (Indeed and Naukri)

- Automated job scraping using:
  - BeautifulSoup
  - Selenium + WebDriver Manager
- Extracts:
  - Title
  - Company
  - Location
  - Salary
  - Full job description
  - Apply link

### 📄 Resume Processing

- Accepts PDF uploads
- Text extraction using:
  - PyMuPDF
  - PyPDF
- Automatic preprocessing + splitting
- Vector embedding with Sentence Transformers

### ⏰ Automated Job Monitoring

- Users can schedule automatic job scraping:
  - **Off**
  - **Daily**
  - **Weekly**
- Scheduler runs in the background using **Celery + Redis**
- Each scheduled run:
  - Scrapes new jobs based on user-defined title and location
  - Matches jobs against resume embeddings
  - Computes similarity scores
  - Sends an **email notification** when a job exceeds a fit threshold (e.g. ≥ 0.6)
- Fully async and non-blocking for the main API

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

  ### 📧 Email Notifications

- Triggered automatically by background workers
- Sent when a job exceeds a similarity threshold
- Includes:
  - Job title
  - Company
  - Match score
  - Apply link
- Delivered to the user’s registered email address

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
- **ImageKit** – External storage for resume pdf's
- **ChromaDB** – Vector database for semantic search
- **Sentence Transformers** – Embedding model for resume + job descriptions
- **LangChain Text Splitters** – Chunking for RAG pipeline
- **PyMuPDF & PyPDF** – Resume text extraction
- **Selenium + BeautifulSoup** – Job scraping from Indeed and Naukri
- **Groq LLM API** – Fast LLM inference for chatbot responses
- **Celery** – Distributed background task processing
- **Redis** – Message broker & scheduler backend
- **Celery RedBeat** – Persistent periodic task scheduler
- **Uvicorn** – ASGI server
- **Docker & Docker Compose** – Redis & Celery services

---

## 🚀 How to Run

### 1️⃣ Clone the repository

```bash
git clone <repo-url>
cd RAG-Job-Finder-Chatbot
```

### 2️⃣ Create a virtual environment

```bash
py -3.10 -m venv .venv
source .venv/bin/activate      # Linux / Mac
.venv\Scripts\activate         # Windows
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Set up environment variables

Set up your environment varialbles in `.env` as in `env_example.txt`

### 5️⃣ Set up Celery & Redis services

These services are required for scheduled job scraping and email notifications.

#### 🔹 Start Redis (Docker)

Open a new terminal (terminal 2).

```bash
cd RAG-Job-Finder-Chatbot
docker compose up --build
```

#### 🔹 Start Celery Worker

Open another new terminal (terminal 3).

```bash
cd RAG-Job-Finder-Chatbot

.venv\Scripts\activate         # Windows
# or
source .venv/bin/activate      # Linux / Mac

set PYTHONPATH=.               # Windows
# or
export PYTHONPATH=.            # Linux / Mac

celery -A worker.app worker --loglevel=info --pool=solo

```

### 5️⃣ Run the server (from the first terminal)

```bash
uvicorn api.main:app --reload
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

**POST** `/scrape`  
Scrapes from Indeed and Naukri and stores full job data.

### ✔ Configure the scheduler

**POST** `/schedule-scraper`

- Parameters:

  - Job title
  - Location
  - Frequency: off | daily | weekly

- Creates or updates a background scheduled task

### ✔ Upload Resume

**POST** `/upload_resume`  
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
