# backend/main.py
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import os
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Annotated

try:
    from .config import Config
    from .llm_client import LLMClient
except ImportError:
    from config import Config
    from llm_client import LLMClient

os.makedirs(os.path.dirname(Config.LOG_FILE) or ".", exist_ok=True)

logging.basicConfig(
    filename=Config.LOG_FILE,
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("student_support_backend")

llm_client = LLMClient()
feedback_store: list[dict[str, Any]] = []


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("=" * 50)
    logger.info("Application starting")
    logger.info("Model: %s", Config.MODEL_NAME)
    logger.info("Ollama Host: %s", Config.OLLAMA_HOST)
    logger.info("API Port: %s", Config.API_PORT)

    model_status = llm_client.get_model_status()
    logger.info("Model status: %s", model_status["status"])
    logger.info("=" * 50)

    yield

    logger.info("Application shutting down")


app = FastAPI(
    title="University Student Support Assistant API",
    description="A polished student support assistant powered by a local LLM",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    question: Annotated[
        str,
        Field(
            min_length=1,
            max_length=500,
            json_schema_extra={"example": "How do I register for courses?"},
        ),
    ]
    conversation_context: list[str] | None = None


class AskResponse(BaseModel):
    question: str
    response: str
    model: str
    status: str
    service: str
    timestamp: str
    metadata: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: str
    status: str
    timestamp: str


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    question: str
    response: str
    rating: Literal["Good", "Average", "Poor"]
    service: str = "general"


class FeedbackResponse(BaseModel):
    status: str
    message: str
    timestamp: str


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = exc.errors()
    message = "Invalid request payload"
    if details and details[0].get("loc") and details[0]["loc"][-1] == "question":
        message = details[0].get("msg", "Question cannot be empty")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": message,
            "details": details,
            "status": "error",
            "timestamp": datetime.now().isoformat(),
        },
    )


@app.post("/feedback", response_model=FeedbackResponse)
async def record_feedback(request: FeedbackRequest) -> FeedbackResponse:
    feedback_store.append(
        {
            "question": request.question,
            "response": request.response,
            "rating": request.rating,
            "service": request.service,
            "timestamp": datetime.now().isoformat(),
        }
    )
    logger.info("Recorded %s feedback for %s", request.rating, request.service)

    return FeedbackResponse(
        status="success",
        message="Feedback recorded",
        timestamp=datetime.now().isoformat(),
    )


@app.get("/feedback/summary")
async def feedback_summary() -> dict[str, Any]:
    ratings = {"Good": 0, "Average": 0, "Poor": 0}
    by_service: dict[str, dict[str, int]] = {}

    for entry in feedback_store:
        rating = entry["rating"]
        service = entry.get("service", "general")
        ratings[rating] += 1
        by_service.setdefault(service, {"Good": 0, "Average": 0, "Poor": 0})
        by_service[service][rating] += 1

    return {
        "total": len(feedback_store),
        "ratings": ratings,
        "by_service": by_service,
        "recent": feedback_store[-10:],
    }


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "message": "University Student Support Assistant API",
        "version": "1.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check() -> dict[str, Any]:
    logger.info("Health check requested")
    model_status = llm_client.get_model_status()
    is_healthy = model_status["status"] == "available"

    return {
        "status": "healthy" if is_healthy else "degraded",
        "model": Config.MODEL_NAME,
        "ollama_host": Config.OLLAMA_HOST,
        "timestamp": datetime.now().isoformat(),
        "model_details": model_status,
    }


@app.post(
    "/ask",
    response_model=AskResponse,
    responses={
        200: {"description": "Successfully generated response"},
        400: {"description": "Invalid question", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse},
    },
)
async def ask_question(request: QuestionRequest) -> AskResponse:
    try:
        question_text = request.question.strip()
        logger.info("Received question: %s", question_text)

        if not question_text:
            logger.warning("Empty question received")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty")

        llm_response = llm_client.generate_response(
            question_text,
            conversation_history=request.conversation_context or [],
        )

        if "error" in llm_response:
            logger.error("Model error: %s", llm_response["error"])
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=llm_response["error"])

        response_preview = llm_response["response"][:100]
        logger.info("Generated response: %s...", response_preview)

        return AskResponse(
            question=question_text,
            response=llm_response["response"],
            model=llm_response.get("model", Config.MODEL_NAME),
            status="success",
            service=llm_response.get("service", "general"),
            timestamp=datetime.now().isoformat(),
            metadata=llm_response.get("metadata"),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected error: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(exc)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=Config.API_HOST, port=Config.API_PORT, reload=True)
