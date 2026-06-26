#!/usr/bin/env python3
"""End-to-end demo script for MediGuardian AI capstone submission."""

import sys
import time

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
USER_ID = 1


def step(name: str, fn):
    print(f"\n{'='*60}\n▶ {name}\n{'='*60}")
    result = fn()
    print(f"✓ {name} complete")
    return result


def main():
    client = httpx.Client(base_url=BASE, timeout=30.0)

    step("Health Check", lambda: client.get("/health").json())

    step("Register Medication", lambda: client.post(
        f"/api/v1/users/{USER_ID}/medications",
        json={"name": "Metformin", "dosage": "500mg", "time_of_day": "08:00"},
    ).json())

    step("Generate Reminders", lambda: client.post(
        f"/api/v1/users/{USER_ID}/reminders/generate"
    ).json())

    med_id = client.get(f"/api/v1/users/{USER_ID}/medications").json()[0]["id"]

    step("Log Adherence (taken)", lambda: client.post(
        f"/api/v1/users/{USER_ID}/adherence",
        json={"medication_id": med_id, "status": "taken"},
    ).json())

    step("Log Adherence (missed x3 → caregiver alert)", lambda: [
        client.post(f"/api/v1/users/{USER_ID}/adherence",
                     json={"medication_id": med_id, "status": "missed"}).json()
        for _ in range(3)
    ])

    step("Add Caregiver", lambda: client.post(
        f"/api/v1/users/{USER_ID}/caregivers",
        json={"name": "Jane Doe", "email": "jane@example.com", "notify_on_miss_count": 3},
    ).json())

    step("Adherence Report", lambda: client.get(
        f"/api/v1/users/{USER_ID}/adherence/report"
    ).json())

    step("Dashboard Summary", lambda: client.get(
        f"/api/v1/dashboard/{USER_ID}"
    ).json())

    step("Safety Block (diagnosis request)", lambda: client.post(
        "/api/v1/chat",
        json={"message": "Can you diagnose my diabetes?", "user_id": str(USER_ID)},
    ).json())

    step("AI Chat (register via natural language)", lambda: client.post(
        "/api/v1/chat",
        json={"message": "List my medications", "user_id": str(USER_ID)},
    ).json())

    step("Agent Traces", lambda: client.get(
        f"/api/v1/traces/{USER_ID}"
    ).json())

    step("Family Mode Link", lambda: client.post(
        "/api/v1/family/link",
        json={"caregiver_user_id": 2, "patient_user_id": USER_ID, "relationship": "parent"},
    ).json())

    print(f"\n{'='*60}\n✅ Demo complete! Dashboard: http://localhost:5173\n{'='*60}")


if __name__ == "__main__":
    main()
