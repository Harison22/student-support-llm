
# Task 9: Industry Production Reflection

### 1. What are the main components of your deployed LLM system?

Our deployed system follows a decoupled, three-tier architecture:

* **Frontend Interface:** A responsive web dashboard built with **Streamlit** configured in a `wide` layout. It features a left-hand **sidebar navigation menu** for direct access to pre-set Frequently Asked Questions (FAQs) alongside a centralized interactive chat interface styled with custom CSS.
* **Backend API:** An asynchronous **FastAPI** application acting as the orchestration layer that handles cross-origin policies (CORS), input validation, application logging, and structured user feedback routing.
* **Retrieval-Augmented Generation (RAG) Core:** A file-based context retrieval engine (`faq.txt`) dynamically parsed by a keyword-matching scoring algorithm built directly into the backend orchestration logic.
* **Local LLM Engine:** An **Ollama** server hosting the local large language model, which handles high-performance natural language inference using local compute infrastructure.

---

### 2. Why is FastAPI useful in this pipeline?

FastAPI serves as an exceptional backend orchestrator for several reasons:

* **Asynchronous Performance:** Built on Starlette and Uvicorn, its native asynchronous execution capabilities (`async def`) prevent the server from blocking threads while waiting for long-running local LLM inference tasks to finish.
* **Data Validation:** Using strict **Pydantic** data models (`QuestionRequest`, `AskResponse`), it enforces strong type-checking at the gateway level, automatically filtering and rejecting empty or malformed requests.
* **Self-Documentation:** It instantly generates and hosts interactive OpenAPI documentation (`/docs` via Swagger UI), streamlining API testing, debugging, and cross-team integration workflows.

---

### 3. What role does your chosen LLM model play?

The local LLM serves as the cognitive text generation engine. Instead of answering raw student queries blindly or generic campus questions untruthfully, it acts as a **context-aware generator**. It interprets the intent behind the student's question alongside the targeted reference text blocks fetched and injected by the RAG layer, compiling a fluid, concise, and contextually accurate answer.

---

### 4. What role does the frontend play?

The **Streamlit** frontend governs the entire user presentation layer and user experience. It systematically manages state variables for chat logs (`st.session_state`), styles layout wrappers using embedded CSS blocks to render user messages on the right and assistant answers on the left, handles UI elements like background spinners during token generation, and triggers direct endpoint inquiries to the FastAPI backend.

---

### 5. What is the difference between running the model locally and using an external API?

| Metric | Local Deployment (Ollama) | External API (e.g., OpenAI) |
| --- | --- | --- |
| **Data Privacy** | **High;** all student queries and data stay strictly on the local machine. | **Low;** private data is transmitted to third-party corporate servers. |
| **Operational Cost** | **Zero ongoing usage fees;** execution capital costs are fixed to the local hardware. | **Variable cost;** priced via usage-based credit models per thousand tokens processed. |
| **Internet Dependency** | Runs **100% offline** without any network dependency. | Requires a continuous, high-speed internet connection to operate. |
| **Scalability & Power** | Strictly limited by local computing specs (GPU VRAM, System RAM). | Highly scalable; runs on high-capacity global cloud infrastructure. |

---

### 6. What security risks may exist if this system is deployed in an organisation?

* **Data Exposure:** Exposing the raw FastAPI backend over an open local area network (LAN) without credential tracking or token-based gateways could allow unauthorized internal actors to hijack system logs.
* **Prompt Injection:** Malicious users could input adversarial phrases into the prompt workspace explicitly designed to overwrite the system's background guidelines, forcing the underlying model to break rules or hallucinate.
* **Resource Exhaustion (DoS):** Because local LLM text generation is highly compute-heavy on GPU and CPU processors, a sudden influx of automated, concurrent questions could easily lock up the system.

---

### 7. What improvements would be needed before deploying this system in production?

* **Vector Database Integration:** Transitioning from file-based keyword matching to a proper semantic vector storage system (such as ChromaDB or FAISS) to calculate contextual distance using dense text embeddings.
* **Production API Gateway:** Adding an explicit **Nginx** reverse proxy to route traffic, setting up secure token validation through **OAuth2/JWT**, and establishing rate-limiting protocols.
* **Database Persistence:** Moving beyond temporary session lists to solid transactional databases (like PostgreSQL or MongoDB) to store historical telemetry logs and long-term feedback entries.

---

### 8. How would you monitor the system in real-world use?

* **Performance Telemetry:** Incorporating infrastructure scrapers like Prometheus paired with Grafana dashboards to keep track of response latencies, server traffic, and hardware strain (GPU VRAM allocation, CPU spikes).
* **User Satisfaction Audits:** Evaluating data stored from the backend's `/feedback/summary` path to calculate user approval distributions ("Good", "Average", "Poor") over time and catch failing responses.

---

### 9. How would you protect sensitive student information?

* **Data Masking and Scrubbing:** Integrating regex patterns or Named Entity Recognition (NER) filtering on the backend router to scan, scrub, and eliminate any Personally Identifiable Information (PII)—like student phone numbers or registration numbers—before saving system telemetry.
* **Network Encryption:** Enforcing HTTPS/TLS transport encryption protocols to lock down all communication links traveling between user browsers and the servers.
* **Role-Based Access Control (RBAC):** Restricting access permissions to administrative analytical dashboards, log readouts, and database layers to authorized administrative staff only.

---

### 10. What challenges did you face during implementation?

* **Branch Merge Conflicts:** Manually identifying and reconciling contradictory code changes when merging structural frontend interface adjustments with core layout edits from team members.
* **Shell Rendering Constraints:** Debugging environment execution errors (such as `PSReadLine` buffer space faults in Windows PowerShell) caused by deep system directory links with spaces during virtual environment initialization.
* **UI Structure and Layout Optimization:** Restructuring the user layout from basic vertical listings into a clean dashboard design—using specialized sidebar blocks—to display reference FAQs cleanly without crowding the primary conversation feed.
* **Context Anchoring:** Engineering prompt wrappers that reliably instruct the local model to favor the explicit guidelines in `faq.txt` over its base training weights without hallucinating wrong facts.
