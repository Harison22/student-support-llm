import requests
import json

def test_ollama():
    """Test if Ollama is working properly"""
    print("Testing Ollama connection...")
    
    try:
        # Check if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running!")
            models = response.json().get('models', [])
            print("\n Available models:")
            for model in models:
                print(f"  - {model['name']} ({model['size']} bytes)")
            
            # Test model response
            test_prompt = "Hello, this is a test. Reply with: OK"
            payload = {
                "model": "llama3.2:1b",
                "prompt": test_prompt,
                "stream": False
            }
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("\n Testing model response:")
                print(f"Response: {result.get('response', '')[:50]}...")
                print("✅ Model is working correctly!")
                return True
            else:
                print("❌ Model test failed!")
                return False
                
        else:
            print("❌ Ollama is not responding!")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama!")
        print("   Make sure to run: ollama serve")
        return False

if __name__ == "__main__":
    test_ollama()
