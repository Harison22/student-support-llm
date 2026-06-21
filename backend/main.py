# backend/main.py
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import json

from config import Config
from llm_client import LLMClient

# Setup logging
logging.basicConfig(
    filename=Config.LOG_FILE,
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="University Student Support Assistant API",
    description="API for university student support using local LLM",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM client
llm_client = LLMClient()

# Request/Response Models
class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, 
                          example="How do I register for courses?")

class AskResponse(BaseModel):
    question: str
    response: str
    model: str
    status: str
    timestamp: str
    metadata: dict = None

class ErrorResponse(BaseModel):
    error: str
    status: str
    timestamp: str

# ---------- ENDPOINTS ----------

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": "University Student Support Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Checks:
    1. API is running
    2. Member 1A's model is available
    """
    logger.info("Health check requested")
    
    # Check Member 1A's model status
    model_status = llm_client.get_model_status()
    
    # Determine overall health
    is_healthy = model_status["status"] == "available"
    
    return {
        "status": "healthy" if is_healthy else "degraded",
        "model": Config.MODEL_NAME,
        "ollama_host": Config.OLLAMA_HOST,
        "timestamp": datetime.now().isoformat(),
        "model_details": model_status
    }

@app.post(
    "/ask",
    response_model=AskResponse,
    responses={
        200: {"description": "Successfully generated response"},
        400: {"description": "Invalid question", "model": ErrorResponse},
        500: {"description": "Server error", "model": ErrorResponse}
    }
)
async def ask_question(request: QuestionRequest):
    """
    Ask a question to the assistant
    
    This endpoint:
    1. Receives question from frontend
    2. Sends to Member 1A's model via Ollama
    3. Returns the generated response
    """
    try:
        question_text = request.question.strip()
        logger.info(f"Received question: {question_text}")
        
        # Validate question
        if not question_text:
            logger.warning("Empty question received")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )
        
        # Get response from Member 1A's model
        llm_response = llm_client.generate_response(question_text)
        
        # Check for errors
        if "error" in llm_response:
            logger.error(f"Model error: {llm_response['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=llm_response["error"]
            )
        
        # Log the response
        response_preview = llm_response["response"][:100]
        logger.info(f"Generated response: {response_preview}...")
        
        # Return success
        return AskResponse(
            question=question_text,
            response=llm_response["response"],
            model=llm_response.get("model", Config.MODEL_NAME),
            status="success",
            timestamp=datetime.now().isoformat(),
            metadata=llm_response.get("metadata")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

# ---------- STARTUP/SHUTDOWN ----------

@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("=" * 50)
    logger.info("Application Starting")
    logger.info(f"Model: {Config.MODEL_NAME}")
    logger.info(f"Ollama Host: {Config.OLLAMA_HOST}")
    logger.info(f"API Port: {Config.API_PORT}")
    
    # Check Member 1A's model status
    model_status = llm_client.get_model_status()
    logger.info(f"Model Status: {model_status['status']}")
    logger.info("=" * 50)

@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information"""
    logger.info("Application shutting down")

# ---------- RUN SERVER ----------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=True
    )