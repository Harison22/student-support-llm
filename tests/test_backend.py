import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app, feedback_store


class BackendImprovementsTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, raise_server_exceptions=False)
        feedback_store.clear()

    def test_sanitizes_and_classifies_student_question(self):
        with patch("backend.main.llm_client.generate_response") as mock_generate:
            mock_generate.return_value = {
                "response": "You can register through the portal.",
                "model": "test-model",
                "status": "success",
                "timestamp": "now",
                "service": "enrollment",
                "metadata": {"service": "enrollment"},
            }

            response = self.client.post(
                "/ask",
                json={"question": "   How do I register for courses?   "},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["question"], "How do I register for courses?")
        self.assertEqual(payload["service"], "enrollment")
        self.assertEqual(payload["metadata"]["service"], "enrollment")

    def test_rejects_empty_questions(self):
        response = self.client.post("/ask", json={"question": "   "})
        self.assertEqual(response.status_code, 400)

    def test_records_feedback_and_returns_summary(self):
        response = self.client.post(
            "/feedback",
            json={
                "question": "How do I reset my portal password?",
                "response": "Use the portal reset link.",
                "rating": "Good",
                "service": "technical_support",
            },
        )

        self.assertEqual(response.status_code, 200)
        summary = self.client.get("/feedback/summary").json()
        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["ratings"]["Good"], 1)
        self.assertEqual(summary["by_service"]["technical_support"]["Good"], 1)

    def test_rejects_invalid_feedback_rating(self):
        response = self.client.post(
            "/feedback",
            json={
                "question": "Question",
                "response": "Answer",
                "rating": "Excellent",
                "service": "general",
            },
        )

        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
