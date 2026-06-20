# 🏥 MediGuardian AI

> **An AI Concierge Agent for Intelligent Medication Management**

MediGuardian AI is a multi-agent medication management assistant built with **Google ADK**, **Gemini**, and **FastAPI**. It helps users organize medication schedules, receive reminders, track adherence, and coordinate with caregivers while maintaining strong AI safety guardrails.

---

## 🚀 Features

- 🤖 Multi-Agent Architecture
- 💊 Medication Management
- 🧠 Persistent Memory
- ⏰ Smart Reminders
- 👨‍👩‍👧 Caregiver Notifications
- 📊 Adherence Analytics
- 🛡 Responsible AI Guardrails
- ☁ Google Cloud Run Deployment

---

## 🏗 Architecture

```text
User
   │
   ▼
Coordinator Agent
   │
   ├── Medication Agent
   ├── Memory Agent
   ├── Reminder Agent
   ├── Safety Agent
   ├── Caregiver Agent
   └── Analytics Agent
```

---

## Technology Stack

| Technology | Purpose |
|------------|---------|
| Google ADK | Multi-agent framework |
| Gemini | Large Language Model |
| FastAPI | REST API |
| SQLite | Development database |
| PostgreSQL | Production database |
| APScheduler | Reminder scheduling |
| Docker | Containerization |
| Google Cloud Run | Deployment |

---

## Project Structure

```text
app/
agents/
tools/
database/
memory/
api/
docs/
tests/
```

---

## Roadmap

- [x] Project Planning
- [ ] Environment Setup
- [ ] Coordinator Agent
- [ ] Medication Agent
- [ ] Memory Agent
- [ ] Reminder Agent
- [ ] Notification Tool
- [ ] Caregiver Agent
- [ ] Safety Agent
- [ ] Analytics Agent
- [ ] Database
- [ ] Backend API
- [ ] Frontend
- [ ] Evaluation
- [ ] Deployment

---

## Installation

```bash
git clone https://github.com/yosephtesfaye/MediGuardian.git

cd MediGuardian

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file using `.env.example`.

Run:

```bash
uvicorn app.main:app --reload
```

---

## Future Improvements

- Voice reminders
- Smart wearable integration
- OCR prescription scanning
- Calendar synchronization
- Mobile application

---

## Disclaimer

MediGuardian AI is an educational and productivity application.

It does **not** diagnose diseases, prescribe medications, or replace healthcare professionals.

---

## Author

Yoseph Tesfaye