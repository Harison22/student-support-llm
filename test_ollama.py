import pytest
import requests


def test_ollama():
    """Smoke test the optional local Ollama service."""
    print("Testing Ollama connection...")

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            pytest.skip("Ollama is not responding on http://localhost:11434.")

        print("Ollama is running.")
        models = response.json().get("models", [])
        print("\nAvailable models:")
        for model in models:
            print(f"  - {model['name']} ({model['size']} bytes)")

        payload = {
            "model": "llama3.2:1b",
            "prompt": "Hello, this is a test. Reply with: OK",
            "stream": False,
        }

        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30,
        )

        assert response.status_code == 200
        result = response.json()
        print("\nTesting model response:")
        print(f"Response: {result.get('response', '')[:50]}...")

    except requests.exceptions.ConnectionError:
        pytest.skip("Ollama is not running. Start it with: ollama serve")
    except requests.exceptions.Timeout:
        pytest.skip("Ollama did not respond before the smoke-test timeout.")


if __name__ == "__main__":
    test_ollama()
