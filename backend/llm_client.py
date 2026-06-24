# backend/llm_client.py
import requests
from typing import Dict, Any
from datetime import datetime
import logging
from backend.config import Config

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Client for communicating with Member 1A's Ollama LLM
    This connects to the model that Member 1A set up
    """
    
    def __init__(self):
        """Initialize the LLM client"""
        self.model = Config.MODEL_NAME  # Member 1A's model
        self.base_url = Config.OLLAMA_HOST  # Member 1A's Ollama
        self.timeout = Config.OLLAMA_TIMEOUT
        self.is_available = False
        self._check_availability()
    
    def _check_availability(self) -> bool:
        """
        Check if Member 1A's Ollama service is available
        
        Returns:
            bool: True if available, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                self.is_available = True
                logger.info(f"Connected to Ollama at {self.base_url}")
                return True
            else:
                self.is_available = False
                logger.warning("Ollama service is not responding properly")
                return False
        except Exception as e:
            self.is_available = False
            logger.error(f"Ollama service unavailable: {str(e)}")
            return False
    
    def generate_response(self, question: str) -> Dict[str, Any]:
        """
        Send question to Member 1A's model and get response
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with response or error details
        """
        # Check if Member 1A's Ollama is available
        if not self.is_available:
            return {
                "error": "Model service unavailable. Please run: ollama serve",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
        
        # Validate input
        if not question or not question.strip():
            return {
                "error": "Question cannot be empty",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Prepare request for Member 1A's model
            payload = {
                "model": self.model,  # Use Member 1A's model
                "prompt": question,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            # Send to Member 1A's Ollama
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
                "metadata": {
                    "total_duration": result.get("total_duration", 0),
                    "eval_count": result.get("eval_count", 0)
                }
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timed out after {self.timeout} seconds")
            return {
                "error": "Model is taking too long to respond",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama service")
            self.is_available = False
            return {
                "error": "Cannot connect to model service",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "error": f"An error occurred: {str(e)}",
                "status": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current status of Member 1A's model"""
        if not self.is_available:
            return {
                "status": "unavailable",
                "model": self.model,
                "message": "Ollama service is not running"
            }
        
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_found = any(m.get("name") == self.model for m in models)
                
                return {
                    "status": "available" if model_found else "not_found",
                    "model": self.model,
                    "message": "Model is ready" if model_found else "Model not found"
                }
        except Exception:
            return {
                "status": "unavailable",
                "model": self.model,
                "message": "Cannot check model status"
            }