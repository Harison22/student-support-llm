# backend/llm_client.py
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

try:
    from .config import Config
    from .prospectus import ProspectusMatch, ProspectusRetriever
except ImportError:
    from config import Config
    from prospectus import ProspectusMatch, ProspectusRetriever

logger = logging.getLogger("student_support_llm_client")


class LLMClient:
    """
    Client for communicating with the Ollama-backed student support assistant.
    Handles question sanitization, classification, prompt building, and
    response generation using the local LLM model.
    """

    def __init__(self) -> None:
        self.model = Config.MODEL_NAME
        self.base_url = Config.OLLAMA_HOST
        self.timeout = Config.OLLAMA_TIMEOUT
        self.max_tokens = Config.OLLAMA_MAX_TOKENS
        self.prospectus = ProspectusRetriever(
            Config.PROSPECTUS_PATH,
            Config.PROSPECTUS_INDEX_PATH
        )
        self.is_available = False
        self._check_availability()

    def _check_availability(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self.is_available = True
                logger.info("Connected to Ollama at %s", self.base_url)
                return True

            self.is_available = False
            logger.warning("Ollama service is not responding properly")
            return False
        except Exception as exc:
            self.is_available = False
            logger.error("Ollama service unavailable: %s", str(exc))
            return False

    def sanitize_question(self, question: str) -> str:
        cleaned = " ".join((question or "").split())
        cleaned = cleaned.replace("\n", " ").strip()
        if "<" in cleaned and ">" in cleaned:
            cleaned = cleaned.replace("<", "").replace(">", "")
        return cleaned

    def classify_question(self, question: str) -> str:
        lowered = question.lower()
        service_keywords = {
            "enrollment": [
                "register", "registration", "course", "enroll",
                "schedule", "semester", "class", "programme",
                "admission", "application", "academic calendar",
                "department", "faculty", "student portal"
            ],
            "financial_aid": [
                "financial", "aid", "scholarship", "fee", "tuition",
                "payment", "cost", "funding", "bursary", "loan",
                "sponsorship", "budget", "receipt"
            ],
            "housing": [
                "housing", "dorm", "residence", "accommodation", "room",
                "hostel", "hostels", "living", "campus housing",
                "dormitory", "rent", "utilities"
            ],
            "academic_support": [
                "study", "tutor", "exam", "grade", "academic",
                "library", "learning", "assignment", "project",
                "research", "supervisor", "lecture", "tutorial",
                "thesis", "dissertation"
            ],
            "technical_support": [
                "portal", "login", "password", "tech", "system",
                "wifi", "email", "computer", "internet", "network",
                "account", "access", "password reset"
            ],
        }

        for service, keywords in service_keywords.items():
            if any(keyword in lowered for keyword in keywords):
                return service
        return "general"

    def build_prompt(
        self,
        question: str,
        service: str,
        conversation_history: Optional[List[str]] = None,
        prospectus_matches: Optional[List[ProspectusMatch]] = None,
    ) -> str:
        # UDSM-specific templates (without the repetitive disclaimer)
        templates = {
            "enrollment": (
                "You are a helpful UDSM enrollment advisor. "
                "Answer the student's question about registration, courses, "
                "or academic planning at the University of Dar es Salaam. "
                "Keep the response clear, helpful, and under 120 words. "
                "Finish with a complete sentence."
            ),
            "financial_aid": (
                "You are a supportive UDSM financial aid assistant. "
                "Help the student understand scholarships, tuition, fees, "
                "or payment options at the University of Dar es Salaam. "
                "Keep the response under 120 words."
            ),
            "housing": (
                "You are a helpful UDSM housing advisor. "
                "Answer the student's question about hostels, dormitories, "
                "or accommodation at the University of Dar es Salaam. "
                "Keep the response under 120 words."
            ),
            "academic_support": (
                "You are a UDSM academic support specialist. "
                "Answer questions about studying, tutoring, exams, grades, "
                "or library services at the University of Dar es Salaam. "
                "Keep the response under 120 words."
            ),
            "technical_support": (
                "You are a UDSM tech support guide. "
                "Help the student with student portals, login issues, "
                "passwords, or general tech access at UDSM. "
                "Keep the response under 120 words."
            ),
        }

        prompt = templates.get(
            service,
            "You are a helpful UDSM student support assistant. "
            "Answer the student's question about the University of Dar es Salaam. "
            "Keep the response under 120 words."
        )

        # Add conversation history
        if conversation_history:
            recent_context = "\n".join(conversation_history[-4:])
            prompt = f"{prompt}\n\nConversation context:\n{recent_context}"

        # Add prospectus context if available
        if prospectus_matches:
            context = "\n\n".join(
                f"From UDSM Prospectus (page {match.page}): {match.text}"
                for match in prospectus_matches
            )
            prompt = (
                f"{prompt}\n\nUse the UDSM prospectus as your primary source. "
                f"If the prospectus doesn't have the answer, use your general "
                f"knowledge about UDSM or suggest helpful resources.\n\n"
                f"Prospectus Context:\n{context}"
            )
        else:
            # Encourage broader search without the repetitive disclaimer
            prompt = (
                f"{prompt}\n\n"
                f"Use your general knowledge about the University of Dar es Salaam "
                f"to answer the student's question. If you don't know, suggest "
                f"practical resources like the UDSM website, student portal, "
                f"or relevant university offices."
            )

        return prompt

    def generate_response(
        self,
        question: str,
        conversation_history: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        cleaned_question = self.sanitize_question(question)
        if not cleaned_question:
            return {
                "error": "Question cannot be empty",
                "status": "error",
                "timestamp": datetime.now().isoformat(),
            }

        if not self.is_available:
            self._check_availability()

        if not self.is_available:
            return {
                "error": "Model service unavailable. Please run: ollama serve",
                "status": "error",
                "timestamp": datetime.now().isoformat(),
            }

        service = self.classify_question(cleaned_question)
        prospectus_matches = self.prospectus.search(cleaned_question)
        
        # Build the prompt (no repetitive disclaimer added here)
        prompt = self.build_prompt(
            cleaned_question,
            service,
            conversation_history,
            prospectus_matches
        )

        try:
            payload = {
                "model": self.model,
                "prompt": cleaned_question,
                "system": prompt,
                "stream": False,
                "keep_alive": "10m",
                "options": {
                    "temperature": 0.4,
                    "top_p": 0.9,
                    "num_predict": self.max_tokens,
                    "num_ctx": 1024,
                },
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            return {
                "response": result.get("response", "No response generated"),
                "model": self.model,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "service": service,
                "source": (
                    "UDSM Prospectus" if prospectus_matches else "UDSM Knowledge Base"
                ),
                "prospectus_pages": [
                    match.page for match in prospectus_matches
                ],
                "metadata": {
                    "service": service,
                    "total_duration": result.get("total_duration", 0),
                    "eval_count": result.get("eval_count", 0),
                },
            }

        except requests.exceptions.Timeout:
            logger.error("Request timed out after %s seconds", self.timeout)
            return {
                "error": (
                    f"Model is taking too long to respond "
                    f"after {self.timeout} seconds"
                ),
                "status": "error",
                "timestamp": datetime.now().isoformat(),
            }

        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama service")
            self.is_available = False
            return {
                "error": "Cannot connect to model service",
                "status": "error",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as exc:
            logger.error("Unexpected error: %s", str(exc))
            return {
                "error": f"An error occurred: {str(exc)}",
                "status": "error",
                "timestamp": datetime.now().isoformat(),
            }

    def get_model_status(self) -> Dict[str, Any]:
        if not self.is_available:
            return {
                "status": "unavailable",
                "model": self.model,
                "message": "Ollama service is not running",
            }

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_found = any(
                    model.get("name") == self.model for model in models
                )

                return {
                    "status": "available" if model_found else "not_found",
                    "model": self.model,
                    "message": (
                        "Model is ready" if model_found else "Model not found"
                    ),
                }
        except Exception:
            return {
                "status": "unavailable",
                "model": self.model,
                "message": "Cannot check model status",
            }

        return {
            "status": "unavailable",
            "model": self.model,
            "message": "Cannot check model status",
        }