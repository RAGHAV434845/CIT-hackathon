# AI Developer Codebase Understanding & Academic Project Management Platform

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Tailwind)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Landing  │ │ Dashboard│ │ Analysis │ │ Chatbot  │          │
│  │ Page     │ │ (RBAC)   │ │ Views    │ │ Interface│          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Diagrams │ │ Docs     │ │ Security │ │ Faculty  │          │
│  │ Viewer   │ │ Editor   │ │ Report   │ │ Panel    │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└──────────────────────┬──────────────────────────────────────────┘
                       │ REST API (JSON)
┌──────────────────────▼──────────────────────────────────────────┐
│                    BACKEND (Python Flask)                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   API Gateway Layer                      │    │
│  │  Auth Middleware │ Rate Limiter │ CORS │ Request Logger  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │ Auth       │ │ Repo       │ │ Analysis   │ │ Security   │   │
│  │ Service    │ │ Service    │ │ Engine     │ │ Scanner    │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │ README     │ │ Doc        │ │ Diagram    │ │ Chatbot    │   │
│  │ Generator  │ │ Generator  │ │ Generator  │ │ Service    │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                  │
│  │ Analytics  │ │ Faculty    │ │ HOD        │                  │
│  │ Service    │ │ Service    │ │ Service    │                  │
│  └────────────┘ └────────────┘ └────────────┘                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                    DATA LAYER                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │ Firebase Auth  │  │ Firestore DB   │  │ Firebase       │    │
│  │                │  │                │  │ Storage        │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│  ┌────────────────┐                                             │
│  │ Temp File      │  (Cloned repos, uploaded ZIPs)              │
│  │ Storage        │                                             │
│  └────────────────┘                                             │
└─────────────────────────────────────────────────────────────────┘
```

## Firestore Schema Design

### Collection: `users`
```json
{
  "uid": "firebase-auth-uid",
  "username": "string",
  "email": "string",
  "role": "student | faculty | hod",
  "github_link": "string",
  "department": "string",
  "mentor_id": "string | null",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Collection: `repositories`
```json
{
  "repo_id": "auto-generated",
  "owner_uid": "string",
  "name": "string",
  "source": "github | upload",
  "github_url": "string | null",
  "status": "pending | analyzing | completed | failed",
  "analysis_result": {
    "framework": "string",
    "tech_stack": ["string"],
    "entry_points": ["string"],
    "architecture_type": "string",
    "total_files": "number",
    "total_lines": "number",
    "languages": {"python": 1200, "javascript": 300}
  },
  "security_scan": {
    "total_issues": "number",
    "resolved": "number",
    "issues": [
      {
        "type": "api_key | token | password | aws_key",
        "file": "string",
        "line": "number",
        "severity": "high | medium | low",
        "status": "detected | removed | ignored | masked",
        "snippet": "string"
      }
    ]
  },
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Collection: `documents`
```json
{
  "doc_id": "auto-generated",
  "repo_id": "string",
  "owner_uid": "string",
  "type": "readme | api_doc | tech_report | module_breakdown",
  "content": "string (markdown)",
  "format": "markdown | pdf | word",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Collection: `diagrams`
```json
{
  "diagram_id": "auto-generated",
  "repo_id": "string",
  "owner_uid": "string",
  "type": "architecture | flow | dependency",
  "mermaid_code": "string",
  "custom_positions": {},
  "created_at": "timestamp"
}
```

### Collection: `analytics`
```json
{
  "analytics_id": "auto-generated",
  "event_type": "analysis | document | diagram | security_scan | login",
  "user_uid": "string",
  "repo_id": "string | null",
  "metadata": {},
  "created_at": "timestamp"
}
```

### Collection: `projects` (Faculty)
```json
{
  "project_id": "auto-generated",
  "faculty_uid": "string",
  "title": "string",
  "description": "string",
  "student_uids": ["string"],
  "repo_ids": ["string"],
  "scores": {
    "architecture": "number (0-10)",
    "documentation": "number (0-10)",
    "code_quality": "number (0-10)",
    "overall": "number (0-10)"
  },
  "status": "active | completed | archived",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### Collection: `mentor_assignments`
```json
{
  "assignment_id": "auto-generated",
  "hod_uid": "string",
  "faculty_uid": "string",
  "student_uid": "string",
  "department": "string",
  "created_at": "timestamp"
}
```

## Role-Based Access Control (RBAC)

| Resource              | Student | Faculty | HOD   |
|-----------------------|---------|---------|-------|
| Own repositories      | CRUD    | CRUD    | CRUD  |
| Analyze code          | Yes     | Yes     | Yes   |
| Generate docs         | Yes     | Yes     | Yes   |
| View other repos      | No      | Assigned| All   |
| Create project folder | No      | Yes     | Yes   |
| Score projects        | No      | Yes     | Yes   |
| Manage students       | No      | No      | Yes   |
| Manage faculty        | No      | No      | Yes   |
| Assign mentors        | No      | No      | Yes   |
| View analytics        | Own     | Dept    | All   |
| Score faculty          | No      | No      | Yes   |

## API Endpoint Structure

### Auth
- `POST /api/auth/register` — Register user
- `POST /api/auth/login` — Login (Firebase token)
- `GET  /api/auth/profile` — Get profile
- `PUT  /api/auth/profile` — Update profile

### Repositories
- `POST   /api/repos` — Create repo (upload/clone)
- `GET    /api/repos` — List user repos
- `GET    /api/repos/:id` — Get repo details
- `DELETE /api/repos/:id` — Delete repo
- `GET    /api/repos/search?q=` — Search public repos

### Analysis
- `POST /api/analysis/:repo_id` — Start analysis
- `GET  /api/analysis/:repo_id` — Get analysis results
- `GET  /api/analysis/:repo_id/status` — Get analysis status

### Security
- `GET  /api/security/:repo_id` — Get security scan results
- `POST /api/security/:repo_id/resolve` — Resolve issues

### Documentation
- `POST /api/docs/:repo_id/readme` — Generate README
- `POST /api/docs/:repo_id/api-doc` — Generate API doc
- `POST /api/docs/:repo_id/report` — Generate tech report
- `GET  /api/docs/:repo_id` — List documents
- `PUT  /api/docs/:doc_id` — Edit document
- `GET  /api/docs/:doc_id/export/:format` — Export

### Diagrams
- `POST /api/diagrams/:repo_id` — Generate diagram
- `GET  /api/diagrams/:repo_id` — List diagrams
- `PUT  /api/diagrams/:diagram_id` — Update diagram
- `GET  /api/diagrams/:diagram_id/export` — Export image

### Chatbot
- `POST /api/chat/:repo_id` — Send message

### Analytics
- `GET /api/analytics/dashboard` — Dashboard stats
- `GET /api/analytics/user/:uid` — User stats
- `GET /api/analytics/department/:dept` — Department stats

### Faculty
- `POST /api/faculty/projects` — Create project
- `GET  /api/faculty/projects` — List projects
- `PUT  /api/faculty/projects/:id/score` — Score project
- `GET  /api/faculty/students` — List assigned students

### HOD
- `GET    /api/hod/faculty` — List faculty
- `GET    /api/hod/students` — List students
- `POST   /api/hod/assign-mentor` — Assign mentor
- `PUT    /api/hod/faculty/:id/score` — Score faculty
- `GET    /api/hod/analytics` — Department analytics

## Deployment Strategy

### Development
- Backend: Flask dev server (port 5000)
- Frontend: React dev server (port 3000)
- Firebase Emulator Suite for local testing

### Production
- Backend: Gunicorn + Docker on Google Cloud Run
- Frontend: Firebase Hosting (static)
- CI/CD: GitHub Actions
- Monitoring: Firebase Performance + Custom Analytics

## Hackathon MVP (6-Hour Plan)

| Hour | Task |
|------|------|
| 0-1  | Project setup, Firebase config, auth system |
| 1-2  | Repo upload/clone, basic static analysis |
| 2-3  | Framework detection, tech stack detection |
| 3-4  | Security scanner, README generator |
| 4-5  | Mermaid diagram generation, basic chatbot |
| 5-6  | Frontend dashboard, demo prep, deployment |

### MVP Scope:
- Auth (student only)
- Upload ZIP / GitHub clone
- Python + JavaScript analysis
- Framework detection
- Basic security scan
- README generation
- Architecture diagram (Mermaid)
- Simple chatbot
