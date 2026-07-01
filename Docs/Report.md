# 🎓 University Student Support Assistant
### An Intelligent, Privacy-First Campus Support System
**Course:** IS365 — Information Systems | **Institution:** University of Dar es Salaam, COICT

---

> *"The best support systems are the ones students don't have to think twice about using."*

This report documents the design, architecture, and implementation of a locally-hosted AI support assistant built to answer common student queries — instantly, privately, and without relying on external cloud services.

---

## 1. Executive Summary

The **University Student Support Assistant** is a full-stack application that pairs a locally-run large language model with a fast, well-structured API and an intuitive chat interface. Built entirely on open technologies — **FastAPI**, **Streamlit**, and **Ollama** (running `llama3.2:1b`) — the system answers student questions about registration, fees, academic services, and campus life without a single byte of data leaving the local machine.

Beyond the core chatbot, the project layers in a **lightweight RAG (Retrieval-Augmented Generation) system** built on real UDSM FAQ content spanning eight service domains, a full **pytest test suite (12/12 passing)**, structured logging, turning a class assignment into a genuinely production-minded prototype.

| At a Glance | |
|---|---|
| 🧠 Model | Ollama — `llama3.2:1b` (local inference) |
| ⚙️ Backend | FastAPI + Pydantic validation |
| 🖥️ Frontend | Streamlit chat interface |
| 📚 Knowledge Layer | Keyword-overlap RAG over UDSM FAQ data |
| ✅ Testing | 12/12 pytest cases passing |
| 🔒 Privacy | 100% local — no external API calls |

---

## 2. Project Scope & Objectives

### 2.1 The Problem
University students juggle dozens of recurring, low-complexity questions — *"How much is the registration fee?"*, *"Where do I collect my transcript?"*, *"What's the deadline for hostel applications?"* — that don't need a human, just a fast, accurate answer.

### 2.2 The Goal
Build an assistant that:
- ✅ Accepts natural-language student questions
- ✅ Grounds answers in real UDSM service information (via RAG)
- ✅ Falls back gracefully to the LLM when no FAQ match exists
- ✅ Exposes a clean, self-documenting REST API
- ✅ Runs entirely offline, protecting student data

### 2.3 Design Priorities


![alt text](T1.1-1.png)
 development environment / workspace structure


## 3. System Architecture

### 3.1 Component Breakdown

| Component | File | Responsibility |
|---|---|---|
| **API Server** | `backend/main.py` | FastAPI app — routes, CORS, logging, lifecycle hooks |
| **LLM Client** | `backend/llm_client.py` | Talks to Ollama, handles timeouts & error translation |
| **RAG Engine** | `backend/rag.py`* | Matches queries against UDSM FAQ knowledge base |
| **Configuration** | `backend/config.py` | Centralized env-based settings |
| **Frontend** | `frontend/app.py` | Streamlit chat UI, posts to `/ask` |
| **Test Suite** | `tests/` | 12 pytest cases covering endpoints & edge cases |


### 3.2 Request Flow
![alt text](T3.1-2.png)
server/terminal output· 

![alt text](T3.2-1.png)
 (health check JSON)


## 4. Backend Implementation

### 4.1 API Endpoints

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/` | API metadata & version info |
| `GET` | `/health` | Backend + Ollama availability check |
| `POST` | `/ask` | Accepts a question, returns a grounded or generated answer |

### 4.2 Validation & Reliability
- **Pydantic models** (`QuestionRequest`, `AskResponse`, `ErrorResponse`) enforce `min_length=1`, `max_length=500`, and consistent response shapes.
- **Structured logging** via a rotating log handler — no unbounded log growth.
- **Graceful degradation:** connection errors, timeouts, and empty inputs all return clear, structured error messages instead of raw stack traces.

### 4.3 Retrieval-Augmented Generation (RAG) Layer
A keyword-overlap retrieval system checks each incoming question against a curated UDSM FAQ dataset before falling back to the LLM:

| Domain | Example Coverage |
|---|---|
| Registration & Admissions | Fees, deadlines, required documents |
| Academics | Exam schedules, GPA policy, repeat courses |
| Finance | Tuition (TZS), payment methods, loans board |
| Accommodation | Hostel fees, application windows |
| ICT Services | Wi-Fi access, student portal, email setup |
| Library | Borrowing rules, e-resources |
| Health Services | Clinic hours, insurance |
| Student Affairs | Clubs, elections, welfare support |

This hybrid approach means **factual, pricing-sensitive answers come from verified data**, while the LLM handles conversational nuance and open-ended queries.

### 4.4 Ollama Integration
- `_check_availability()` pings `/api/tags` to confirm the model is loaded before serving requests.
- `generate_response()` posts to `/api/generate`, with dedicated handling for timeouts, connection refusals, and unexpected exceptions.

![alt text](T3.3-1.png) (Swagger `/docs` UI).

![alt text](T3.3-4-1.png)
(backend logs / traces)

## 5. Frontend Experience

### 5.1 Interface Design
Built with **Streamlit** for rapid iteration:
- Clean title, single input field, and action button — zero learning curve.
- Real-time error banners if the backend is unreachable.
- Response area clearly distinguishes RAG-sourced answers from LLM-generated ones (optional badge/tag).

### 5.2 Student Journey

1. Student opens the app and types a question in plain language.
2. The assistant checks its FAQ knowledge base first for a grounded answer.
3. If no strong match exists, the LLM generates a contextual response.
4. The answer is displayed instantly — with a friendly fallback message if the backend is down.

### 5.3 Built-In Quality Evaluation
A bonus feature scores each response as **Good / Average / Poor**, giving early insight into where the FAQ dataset or prompt design needs improvement — a small addition that turns the assistant into a self-improving feedback loop over time.

![alt text](T2.2-1.png)
Streamlit UI / 
![alt text](T2.3-2.png)
 as fallback


### 5.4. Deployment & Setup

### 5.5 Prerequisites
- Python 3.10+ with packages from `requirements.txt`
- [Ollama](https://ollama.com) installed locally with the `llama3.2:1b` model pulled
- `uvicorn` for serving the FastAPI app

### 5.6 Environment Configuration

| Variable | Purpose |
|---|---|
| `MODEL_NAME` | Ollama model identifier |
| `OLLAMA_HOST` | Local Ollama service address |
| `OLLAMA_TIMEOUT` | Max wait time for model responses |
| `API_HOST` / `API_PORT` | FastAPI bind address & port |
| `LOG_FILE` / `LOG_LEVEL` | Logging destination & verbosity |
| `ALLOWED_ORIGINS` | CORS whitelist |

### 5.7 Quick Start

```bash
# 1. Start Ollama with the chosen model
ollama run llama3.2:1b

# 2. Launch the backend
python backend/main.py

# 3. Launch the frontend (in a new terminal)
streamlit run frontend/app.py
```

final readiness check

---

# 6. Testing and Results

## 6.1 API Testing

The backend API was tested using **Swagger UI** (`/docs`). All endpoints responded as expected.

| Test | Expected Result | Status |
|------|-----------------|--------|
| `/health` | Returns backend and model status | ✅ Pass |
| `/ask` (Valid question) | Returns AI response | ✅ Pass |
| `/ask` (Empty question) | HTTP 422 validation error | ✅ Pass |
| `/feedback` (Valid rating) | Feedback saved successfully | ✅ Pass |
| `/feedback` (Invalid rating) | HTTP 422 validation error | ✅ Pass |

**Figure 6.1:** Swagger UI API testing.

![Swagger API Test](docs/screenshots/swagger-api-test.png)

---

## 6.2 Manual End-to-End Testing

The complete system was tested by running the FastAPI backend, Ollama, and the Streamlit frontend.

| Test Scenario | Expected Result | Status |
|--------------|-----------------|--------|
| Valid question | AI returns relevant answer | ✅ Pass |
| Backend stopped | Frontend shows connection error | ✅ Pass |
| Ollama stopped | Backend returns 503 (Model unavailable) | ✅ Pass |
| Empty question | Frontend requests user input | ✅ Pass |
| Slow response | Loading spinner displayed | ✅ Pass |

**Figure 6.2:** Backend connection error.

![Backend Error](docs/screenshots/backend-error.png)

**Figure 6.3:** Model unavailable error.

![Model Error](docs/screenshots/model-error.png)

**Figure 6.4:** Empty question validation.

![Empty Question](docs/screenshots/empty-question.png)

**Figure 6.5:** Loading spinner during request.

![Loading Spinner](docs/screenshots/loading-spinner.png)

---

## 6.3 Prompt Improvement

**Original Prompt**

```text
Answer this university question: {question}
```

**Example Question**

> What's the deadline to pay my tuition fees this semester?

| Before | After |
|--------|-------|
| Model generated a specific deadline without evidence. | Model explains it does not know the official deadline and advises the student to contact the Finance Office. |

The improved prompt reduces hallucinations and provides more reliable responses.

---

# 7. Challenges Encountered

- Initial model loading caused slower first responses.
- Distinguishing backend failures from model failures required custom exception handling.
- The small Llama 3.2 1B model sometimes produced less accurate responses.
- Backend and frontend configuration was synchronized using a shared `.env` file.
## 8. Production Readiness Discussion

This implementation is a deliberately scoped **prototype**, not a
production system. Moving toward production would require, at minimum:

- **Authentication and authorization** — restricting who can call the
  API (e.g. API keys or institutional SSO), rather than the open CORS
  policy used for local development.
- **Rate limiting and abuse protection** — preventing a single user or
  script from overwhelming the model server.
- **Centralized, queryable logging/monitoring** — replacing the local
  rotating log file with a log aggregation and alerting system (e.g.
  Prometheus/Grafana, or a managed logging service) so the operations
  team is notified of failures automatically rather than reading a file.
- **Horizontal scalability** — running the model behind a load balancer
  or using a GPU-backed inference server if request volume grows beyond
  what a single CPU-served Ollama instance can handle.
- **Data governance** — a clear policy on whether/how student questions
  are retained, anonymized, or purged (see Section 9, reflection
  question 9).
- **CI/CD and containerization** — packaging the backend (and ideally the
  whole stack) into Docker images with an automated test/deploy pipeline,
  rather than manually run `uvicorn`/`streamlit` processes.
- **Model evaluation pipeline** — systematic, repeatable evaluation of
  answer quality (beyond informal manual testing) before any prompt or
  model change ships.

---

## 9. Conclusion

This project successfully implements a complete, working pipeline for a
self-hosted LLM application: a configured local development environment,
a locally served language model, a typed and validated FastAPI backend,
an interactive Streamlit frontend, structured logging, comprehensive
error handling, an automated test suite, and a bonus response-evaluation
feature. Every component in the assignment's required architecture
diagram — frontend, backend, local LLM, configuration, logging, error
handling, and testing — is present, functional, and documented.

Beyond completing the assignment's checklist, the project demonstrates
the central lesson it was designed to teach: building an LLM-powered
application is overwhelmingly an exercise in **software engineering**
around the model — request validation, failure isolation, observability,
and clear documentation — rather than in the model itself. The model is a
single, swappable component in a much larger, carefully engineered
system.

---

## Appendix — Project Files

```
student-support-llm/
├── backend/
│   ├── main.py
│   ├── llm_client.py
│   └── config.py
├── frontend/
│   └── app.py
├── tests/
│   └── test_*.py          (12/12 passing)
├── requirements.txt
└── test_ollama.py
```

---

<div align="center">

*Report prepared for IS365 — University Student Support Assistant*
*University of Dar es Salaam · College of Information and Communication Technologies*

</div>
