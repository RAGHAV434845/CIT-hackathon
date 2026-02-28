# AI Developer — Codebase Understanding & Academic Project Management Platform

A full-stack SaaS platform that analyzes GitHub repositories and ZIP uploads using **static code analysis** (AST parsing, regex scanning, folder heuristics) — not ML-based summarization. Built for academic project management with role-based access for Students, Faculty, and HODs.

## Features

- **Static Code Analysis** — Framework/tech stack detection, architecture classification, component detection, API endpoint extraction, import graph building  
- **Security Scanner** — 17+ regex patterns for secrets/credentials with auto-remove, mask, and ignore actions  
- **Auto Documentation** — README, API docs, tech reports, module breakdowns (Markdown & PDF export)  
- **Diagram Generation** — Architecture, flow, and dependency diagrams via Mermaid.js  
- **AI Chatbot** — Deterministic query handling + Gemini API fallback for codebase Q&A  
- **Academic Management** — Faculty creates projects, assigns students/repos, scores work; HOD assigns mentors, scores faculty, views department analytics  
- **RBAC** — Student / Faculty / HOD roles with Firebase Auth  

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask 3.0 |
| Frontend | React 18, Tailwind CSS 3 |
| Database | Firebase Firestore |
| Auth | Firebase Authentication |
| Diagrams | Mermaid.js |
| Charts | Chart.js |
| AI Fallback | Google Gemini API |

## Quick Start

### Prerequisites
- Python 3.11+, Node.js 18+
- Firebase project with Firestore + Authentication enabled
- Google Gemini API key (optional, for chatbot)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env   # Edit with your Firebase credentials
python app.py
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # Edit with your Firebase config
npm start
```

### Docker

```bash
docker-compose up --build
```

## Project Structure

```
cit_hack/
├── backend/
│   ├── app.py                 # Flask factory
│   ├── config.py              # Configuration
│   ├── engine/
│   │   ├── analyzer.py        # Core static analysis
│   │   ├── security_scanner.py
│   │   ├── doc_generator.py
│   │   └── diagram_generator.py
│   ├── services/
│   │   ├── firebase_service.py
│   │   ├── repo_service.py
│   │   └── chatbot_service.py
│   ├── middleware/
│   │   └── auth_middleware.py
│   └── routes/                # 10 Blueprint route files
├── frontend/
│   ├── src/
│   │   ├── pages/             # 12 page components
│   │   ├── components/
│   │   ├── context/
│   │   ├── services/api.js
│   │   └── firebase.js
│   └── public/
├── docker-compose.yml
└── ARCHITECTURE.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register user |
| GET | `/api/repos` | List repos |
| POST | `/api/repos` | Create repo (GitHub/ZIP) |
| POST | `/api/analysis/{id}/start` | Start analysis |
| GET | `/api/security/{id}/scan` | Security scan |
| POST | `/api/docs/{id}/generate` | Generate docs |
| POST | `/api/diagrams/{id}/generate` | Generate diagrams |
| POST | `/api/chat/{id}` | Chat with AI |
| GET | `/api/analytics/dashboard` | Dashboard stats |

See [ARCHITECTURE.md](ARCHITECTURE.md) for full endpoint reference.

## License

MIT
