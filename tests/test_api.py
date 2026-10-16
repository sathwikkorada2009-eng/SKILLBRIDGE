import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import app
from model import create_initial_data


class SkillBridgeApiTests(unittest.TestCase):
    def setUp(self):
        self.data = create_initial_data()
        self.data_patch = patch.object(app, "_data", return_value=self.data)
        self.save_patch = patch.object(app, "save_data")
        self.data_patch.start()
        self.save_patch.start()
        self.client = TestClient(app.app)

    def tearDown(self):
        self.data_patch.stop()
        self.save_patch.stop()

    def test_health_and_class_listing(self):
        self.assertEqual(self.client.get("/api/health").json(), {"status": "ok"})
        response = self.client.get("/api/classes")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 5)
        self.assertEqual(response.json()[0]["seats_remaining"], 10)

    def test_student_search_is_case_insensitive(self):
        response = self.client.get("/api/students", params={"skill": "PYTHON"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json())
        self.assertTrue(
            all(
                any("python" in skill.casefold() for skill in student["skills"])
                for student in response.json()
            )
        )

    def test_booking_and_duplicate_booking(self):
        payload = {"student_name": "Priya Reddy", "class_id": "C101"}
        response = self.client.post("/api/bookings", json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["students"], ["Priya Reddy"])
        duplicate = self.client.post("/api/bookings", json=payload)
        self.assertEqual(duplicate.status_code, 409)

    def test_tutor_cannot_book_own_class(self):
        response = self.client.post(
            "/api/bookings",
            json={"student_name": "Aarav Sharma", "class_id": "C101"},
        )
        self.assertEqual(response.status_code, 400)

    def test_full_class_rejects_booking(self):
        cls = self.data["classes"][0]
        cls["students"] = [
            student["name"]
            for student in self.data["students"]
            if student["name"] != cls["tutor"]
        ][:cls["capacity"]]
        response = self.client.post(
            "/api/bookings",
            json={"student_name": "Aditi Bose", "class_id": "C101"},
        )
        self.assertEqual(response.status_code, 409)

    def test_meeting_link_requires_assigned_tutor_and_https(self):
        base = "/api/classes/C101/meeting-link"
        wrong_tutor = self.client.put(
            base,
            json={"tutor_name": "Priya Reddy", "link": "https://meet.example.com"},
        )
        self.assertEqual(wrong_tutor.status_code, 403)
        insecure_link = self.client.put(
            base,
            json={"tutor_name": "Aarav Sharma", "link": "http://meet.example.com"},
        )
        self.assertEqual(insecure_link.status_code, 422)

    def test_enrolled_student_can_access_published_meeting(self):
        cls = self.data["classes"][0]
        cls["students"].append("Priya Reddy")
        saved = self.client.put(
            "/api/classes/C101/meeting-link",
            json={"tutor_name": "Aarav Sharma", "link": "https://meet.example.com/room"},
        )
        self.assertEqual(saved.status_code, 200)
        meeting = self.client.get(
            "/api/classes/C101/meeting",
            params={"student_name": "Priya Reddy"},
        )
        self.assertEqual(meeting.status_code, 200)
        self.assertEqual(meeting.json()["url"], "https://meet.example.com/room")

    def test_meeting_and_notes_require_enrollment(self):
        meeting = self.client.get(
            "/api/classes/C101/meeting",
            params={"student_name": "Priya Reddy"},
        )
        notes = self.client.get(
            "/api/classes/C101/notes",
            params={"student_name": "Priya Reddy"},
        )
        self.assertEqual(meeting.status_code, 403)
        self.assertEqual(notes.status_code, 403)

    def test_rating_requires_enrollment_and_accepts_valid_score(self):
        payload = {"student_name": "Priya Reddy", "score": 5, "feedback": "Very clear"}
        denied = self.client.post("/api/classes/C101/ratings", json=payload)
        self.assertEqual(denied.status_code, 403)

        self.data["classes"][0]["students"].append("Priya Reddy")
        accepted = self.client.post("/api/classes/C101/ratings", json=payload)
        self.assertEqual(accepted.status_code, 201)
        self.assertEqual(accepted.json()["average_rating"], 5)

        invalid = self.client.post(
            "/api/classes/C101/ratings",
            json={"student_name": "Priya Reddy", "score": 7},
        )
        self.assertEqual(invalid.status_code, 422)

    def test_ai_endpoint_reports_missing_configuration(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            response = self.client.post("/api/ask", json={"question": "Explain recursion"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("OPENAI_API_KEY", response.json()["detail"])

    def test_ai_notes_reports_missing_configuration(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            response = self.client.post(
                "/api/classes/C101/notes",
                data={"tutor_name": "Aarav Sharma"},
                files={"audio": ("lesson.mp3", b"audio", "audio/mpeg")},
            )
        self.assertEqual(response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
