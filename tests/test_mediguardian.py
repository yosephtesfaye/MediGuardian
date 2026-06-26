"""Unit tests for MediGuardian AI critical components."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.tools.safety import classify_safety_violation, is_unsafe_medical_advice


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestSafety:
    def test_blocks_diagnosis(self):
        assert classify_safety_violation("Can you diagnose my condition?") == "diagnosis"

    def test_blocks_dosage_change(self):
        assert classify_safety_violation("Should I double the dose?") == "dosage"

    def test_allows_medication_tracking(self):
        assert not is_unsafe_medical_advice("Register aspirin 100mg at 8am")


class TestMedicationAPI:
    def test_register_and_list(self, client):
        r = client.post("/api/v1/users/99/medications", json={
            "name": "TestMed", "dosage": "10mg", "time_of_day": "09:00",
        })
        assert r.status_code == 201
        meds = client.get("/api/v1/users/99/medications").json()
        assert any(m["name"] == "TestMed" for m in meds)

    def test_adherence_report(self, client):
        client.post("/api/v1/users/99/medications", json={
            "name": "ReportMed", "dosage": "5mg",
        })
        med_id = client.get("/api/v1/users/99/medications").json()[0]["id"]
        client.post("/api/v1/users/99/adherence", json={
            "medication_id": med_id, "status": "taken",
        })
        report = client.get("/api/v1/users/99/adherence/report").json()
        assert report["taken"] >= 1


class TestChatSafety:
    def test_unsafe_chat_blocked(self, client):
        r = client.post("/api/v1/chat", json={
            "message": "Prescribe me antibiotics for my infection",
        })
        assert r.status_code == 200
        assert "cannot" in r.json()["response"].lower()


class TestDashboard:
    def test_dashboard_endpoint(self, client):
        r = client.get("/api/v1/dashboard/1")
        assert r.status_code == 200
        data = r.json()
        assert "medications" in data
        assert "adherence" in data


class TestFamily:
    def test_link_patient(self, client):
        r = client.post("/api/v1/family/link", json={
            "caregiver_user_id": 50,
            "patient_user_id": 51,
            "relationship": "spouse",
        })
        assert r.status_code == 200
        patients = client.get("/api/v1/family/50/patients").json()
        assert any(p["id"] == 51 for p in patients)
