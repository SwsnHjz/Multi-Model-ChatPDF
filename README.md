## Project Overview
A secure, multi-user web application that allows users to upload PDF documents and chat about their contents.
This project implements a highly optimized Retrieval-Augmented Generation (RAG) pipeline. Instead of relying on heavy frameworks like LangChain or FAISS, the core vector search and context retrieval mechanisms were built from scratch using 'scikit-learn' (Cosine Similarity) to ensure the application remains lightweight, fast, and easily deployable on standard hosting environments like cPanel.

## Core Features

### Smart Features
*   **Auto-Summarization:** The moment a PDF is uploaded, the system asynchronously parses the text and instantly generates a concise, highly accurate summary of the document.
*   **Smart Suggested Questions:** Along with the summary, the AI analyzes the context and provides 3 clickable, suggested questions to help jumpstart the user's interaction with the file.
*   **Global Site AI Assistant:** A dedicated, built-in AI chatbot trained specifically on the platform's internal documentation. It acts as a 24/7 customer support agent, answering user questions about how to navigate and use the website in both Arabic and English.

### Model-Agnostic AI Architecture
Seamlessly switches between multiple industry-leading LLMs based on user preference and task requirements:
*   **GPT-4** (OpenAI)
*   **Gemini 2.5 Pro** (Google)
*   **Mistral-Tiny** (Mistral AI)
*   **DeepSeek-R1** (Together.ai)

### High-Performance Async Processing
*   **Concurrent Embedding:** Overcame standard synchronous bottlenecking by utilizing `asyncio` and `HTTPX` with semaphores. The system processes up to 5 document chunks concurrently, drastically reducing the wait time for embedding large PDFs.
*   **Smart Summarization:** Upon upload, the system automatically parses the first 10,000 characters to generate a concise summary and 3 context-aware suggested questions to jumpstart the user's workflow.

### Enterprise-Grade Security & User Management
*   **Authentication & OAuth:** Full user registration flow with email activation and Google OAuth integration.
*   **SaaS "Guest Mode" Logic:** Implemented a secure Freemium model. Unregistered users can use the app via a "Guest Mode" limited to 2 questions. Guests are tracked anonymously using salted IP hashing (`SHA-256`) to protect privacy while preventing API abuse.
*   **Session Isolation:** User document data and extracted chunks are saved in isolated, secure JSON session files, completely preventing cross-user data leakage.

### Dynamic Multilingual UI/UX
*   **Auto-Language Detection:** The system automatically detects whether the uploaded document and user queries are in Arabic or English, dynamically routing localized prompts to the LLM for maximum accuracy.
*   **Responsive UI:** Features real-time upload progress bars, CSS-based Light/Dark theme toggling via `LocalStorage`, and automatic LTR/RTL layout switching.

## Technical Stack
*   **Backend:** Python 3.13, Flask, Asyncio, HTTPX
*   **AI / RAG Pipeline:** OpenAI Embeddings API, Scikit-Learn (`cosine_similarity`), PyMuPDF (`fitz`)
*   **Database & Auth:** SQLite, Flask-SQLAlchemy, Flask-Bcrypt, Flask-Login, Authlib
*   **Frontend:** HTML5, CSS3, JavaScript (ES6+)

 ## 📂 Project Structure
```text
├── app.py                  # Core Flask application and routing
├── models/                 # Isolated handlers for multi-LLM architecture
│   ├── __init__.py         
│   ├── gpt4_handler.py     
│   ├── gemini_handler.py   
│   ├── mistral_handler.py   
│   └── deepseek_handler.py 
├── templates/              # Jinja2 HTML Templates (Chat, Login, Email Auth)
├── static/                 # Custom CSS, JS (Theme toggling, Chat interactivity)
├── uploads/                # Ephemeral storage for incoming PDFs
└── sessions/               # Secure, isolated JSON stores for vectorized document chunks
```
##How to Run Locally?

1. Clone the Repository:
   ```bash
   git clone https://github.com/SwsnHjz/Multi-Model-ChatPDF.git
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a .env file in the root directory and add your API credentials:
   ```env
   OPENAI_API_KEY=your_openai_key
   GEMINI_API_KEY=your_gemini_key
   MISTRAL_API_KEY=your_mistral_key
   DEEPSEEK_API_KEY=your_deepseek_key
   FLASK_SECRET_KEY=your_secret_key
   GOOGLE_CLIENT_ID=your_google_id
   GOOGLE_CLIENT_SECRET=your_google_secret
   ```
4. Initialize the database and start the server:
   ```bash
   flask run
   ```

