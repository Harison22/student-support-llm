# backend/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    """Configuration settings for the backend"""
    
    # Model settings (matches Member 1A's setup)
    MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2:1b")
    
    # Ollama settings (where Member 1A's model runs)
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", 30))
    
    # API settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    
    # Logging
    LOG_FILE = os.getenv("LOG_FILE", "backend/logs/app.log")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS (for frontend connection)
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    @classmethod
    def get_model_info(cls):
        """Return model information (for health checks)"""
        return {
            "model": cls.MODEL_NAME,
            "ollama_host": cls.OLLAMA_HOST,
            "status": "configured"
        }