# SQLGuard — DBMS-Native SQL Injection Detection System

> **First system to embed ML-powered SQL injection detection directly inside the PostgreSQL query parsing pipeline using Abstract Syntax Tree (AST) structural analysis.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-sqlguard.vercel.app-blue)](https://sqlguard.vercel.app)
[![API Docs](https://img.shields.io/badge/API%20Docs-Render-green)](https://sqlguard-7qgb.onrender.com/docs)
[![Python](https://img.shields.io/badge/Python-3.9-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-Vite-cyan)](https://vitejs.dev)

---

## What is SQLGuard?

SQL injection has been the #1 database attack for over 20 years. Every existing defense operates **outside** the database by reading raw query text. When these fail, the database has no way to protect itself.

**SQLGuard changes this.** It embeds an ML-powered detection engine directly inside PostgreSQL's query parsing pipeline. Instead of reading raw SQL text, it analyzes the **Abstract Syntax Tree (AST)** — the structural skeleton of every query — and classifies it as safe or malicious before it executes.

> Hackers can change the words. They cannot change the structure.

---

## Screenshots

### Dashboard Overview
![Dashboard](docs/screenshots/dashboard.png)

### Query Detection
![Detection](docs/screenshots/detect.png)

### Adversarial Benchmark
![Benchmark](docs/screenshots/benchmark.png)

### Query Log
![Query Log](docs/screenshots/query.png)

### Alerts
![Alerts](docs/screenshots/alert.png)

---

## Key Results

| Model | Accuracy | F1 Score | Avg Latency |
|---|---|---|---|
| XGBoost (AST features) | **99.58%** | 0.9960 | 0.9ms |
| Random Forest (AST features) | **99.25%** | 0.9929 | 1.2ms |
| Signature-based baseline | ~60% on obfuscated | — | 0.5ms |

**Adversarial benchmark:** SQLGuard blocked 10/10 obfuscated attacks that bypass signature-based WAF tools.

---

## Features

- AST-based detection — analyzes query structure, not raw text — invariant to obfuscation
- 55 structural features extracted from every query's syntax tree
- Real-time detection — average inference latency under 1ms
- Live dashboard with attack trends, risk distribution, query log, alert management
- Live attack simulator — fire 10 mixed queries at the system in real time
- AST feature explainer — shows exactly which features triggered each detection verdict
- Adversarial benchmark — visual comparison of SQLGuard vs WAF tools on obfuscated attacks
- JWT authentication — secure API with user registration and login
- Full CRUD API — FastAPI with auto-generated /docs interface
- Auto-refresh every 15 seconds

---

## System Architecture
```
User submits SQL query
        ↓
PostgreSQL Query Parser Hook
        ↓
AST Extractor (pglast)
        ↓
55-Feature Extractor
        ↓
XGBoost / Random Forest Classifier
        ↓
BLOCK or ALLOW + saved to PostgreSQL
        ↓
React Dashboard (live updates)
```

---

## Database Schema

8 normalized tables:

| Table | Purpose |
|---|---|
| `users` | User accounts with JWT auth |
| `raw_query` | Every submitted query with metadata |
| `ast_features` | 55 extracted structural features per query |
| `ml_prediction` | Model verdict, confidence, risk level, latency |
| `alert_log` | Blocked query alerts |
| `model_registry` | Trained model versions and accuracy metrics |
| `training_dataset` | 95,161 labeled training samples |
| `audit_trail` | Immutable action log |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite, Recharts, date-fns |
| Backend | FastAPI, Uvicorn, JWT auth |
| Database | PostgreSQL (Supabase) |
| ML Models | XGBoost, Random Forest (scikit-learn) |
| AST Parser | pglast v7 |
| Deployment | Vercel (frontend), Render (API), Supabase (DB) |

---

## Project Structure
```
sqlguard/
├── src/
│   ├── parser/          # AST extraction (pglast)
│   ├── features/        # 55-feature extractor
│   ├── ml/              # Model training and inference
│   └── api/             # FastAPI application
├── dashboard/           # React frontend (Vite)
├── models/              # Trained .pkl model files
├── data/                # Training datasets
├── docs/
│   ├── screenshots/     # Project screenshots
│   └── ieee_paper/      # Research paper
└── requirements.txt
```

---

## Getting Started Locally

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 15+

### Backend Setup
```bash
git clone https://github.com/diyam-03/sqlguard.git
cd sqlguard

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Add your PostgreSQL credentials to .env
uvicorn src.api.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd dashboard
npm install
npm run dev
```

Visit `http://localhost:5173`

---

## API Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/auth/register` | Create account | No |
| POST | `/auth/login` | Login, get JWT | No |
| POST | `/detect` | Analyze SQL query | Yes |
| GET | `/queries` | Get all queries | Yes |
| GET | `/queries/{id}` | Get specific query | Yes |
| PUT | `/queries/{id}` | Update query | Yes |
| DELETE | `/queries/{id}` | Delete query | Yes |
| GET | `/users` | Get all users | Yes |
| POST | `/users` | Create user | Yes |
| DELETE | `/users/{id}` | Delete user | Yes |
| GET | `/alerts` | Get all alerts | Yes |
| PUT | `/alerts/{id}` | Resolve alert | Yes |
| GET | `/stats` | Dashboard statistics | Yes |
| GET | `/stats/trends` | Attack trends over time | Yes |
| GET | `/stats/distribution` | Risk level breakdown | Yes |
| GET | `/models` | Model registry | Yes |

Full interactive docs at `/docs`

---

## Authors

- Diya Mehta — MPSTME, NMIMS Mumbai
- Dev Sheth — MPSTME, NMIMS Mumbai
- Om Parekh — MPSTME, NMIMS Mumbai
- Rugved Tatkare — MPSTME, NMIMS Mumbai

B.Tech Data Science, 2nd Year — 2025-26

---

## License

MIT License