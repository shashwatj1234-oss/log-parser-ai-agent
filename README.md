# Log Analysis App

A minimal full-stack prototype where users can upload logs and enter an incident prompt.  
The backend parses and filters logs based on keywords and error indicators, then calls the **Perplexity Sonar LLM** to highlight relevant lines and estimate cost.  
The frontend provides a simple UI to upload logs, enter prompts, and view results.

---

## ✨ Features
- Upload **NDJSON logs** (one JSON record per line).
- Enter an **incident prompt** (e.g., “cart service is crashing, check logs”).
- **Backend (Flask)**:
  - Parse uploaded logs (NDJSON or JSON array fallback).
  - Filter logs using prompt keywords + incident/error terms.
  - Call **Perplexity Sonar** LLM to analyze relevance.
  - Return summary, relevant log indices, highlighted logs, and cost.
- **Frontend (React + Vite)**:
  - File upload + prompt input form.
  - Display total, filtered, and highlighted logs.
  - Show LLM summary, reasoning, and API cost.

---

## 📂 Project Structure
```text
log-parser-ai-agent/
├── backend/    # Flask backend (log parsing, filtering, LLM call)
├── frontend/   # React + Vite frontend
```
---

## 🖥 Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows PowerShell
pip3 install -r requirements.txt
python3 app.py
```

## 🌐 Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```

## 🔑 Environment Variables
PERPLEXITY_API_KEY : your_api_key_here


----------

## 📘 Filtering and LLM Analysis Approach
1. Parsing and Normalization
- ParserUtil processes NDJSON logs line by line, ignoring invalid records.
- Each entry is normalized with fields: clusterUid, containerId, containerName, log, namespace, podName, stream, timestamp.
- An internal _idx index tracks log order.

2. Filtering
- LogFilter extracts keywords from the prompt, lowercased and without stopwords.
- Logs are scanned across containerName, podName, namespace, log.
- Keyword frequency builds a _score; only matches > 0 kept.
- Logs are sorted by score and top N returned.

3. LLM Analysis
- Filtered logs and prompt are passed to Perplexity Sonar LLM.
- The model produces:
   - summary of incident
   - relevant_log_indices of key entries
   - reason for selection
- Response includes filtered logs, highlights, LLM output, token usage, and cost.