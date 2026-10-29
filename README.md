# HostelFix: Hostel Maintenance and Housekeeping Portal

HostelFix is an IIT Dharwad course project for reporting and tracking hostel maintenance and housekeeping problems. The project is being developed incrementally across milestones: MS-1 and MS-2 established the problem definition and system design, while MS-3 implements the backend foundation, relational data model, database migrations, synthetic seed data, and REST API.

**Current milestone:** MS-3 — backend and database foundation  
**Repository:** https://github.com/hostelfix-iitdh/hostelfix

> The full system vision includes a student-facing portal, staff workflows, administrator analytics, and the proposed SmartReport AI feature. This README distinguishes that planned product vision from the functionality implemented in the current MS-3 backend.

## Table of contents

- [Team](#team)
- [Project background](#project-background)
- [Milestone scope](#milestone-scope)
- [System vision and key features](#system-vision-and-key-features)
- [Roles and complaint lifecycle](#roles-and-complaint-lifecycle)
- [Technology stack](#technology-stack)
- [Architecture](#architecture)
- [Getting started](#getting-started)
- [Database and synthetic seed data](#database-and-synthetic-seed-data)
- [REST API](#rest-api)
- [Testing and validation](#testing-and-validation)
- [Security and privacy](#security-and-privacy)
- [Project structure](#project-structure)
- [Team workflow and contributions](#team-workflow-and-contributions)
- [AI usage](#ai-usage)
- [Acknowledgements](#acknowledgements)

---

## Team

| No. | Name | Roll number | GitHub |
|---:|---|---|---|
| 1 | Narasimha Reddy Boggula | CS26MT002 | [@Narasimha013](https://github.com/Narasimha013) |
| 2 | Aakash Saran V | CS26MT018 | [@AakashSaran018](https://github.com/AakashSaran018) |
| 3 | Suru Rakesh | CS26MT022 | [@cs26mt022](https://github.com/cs26mt022) |

Repository: <https://github.com/hostelfix-iitdh/hostelfix>

## Project background

Residents may notice problems such as dirty corridors, overflowing dustbins, broken lights, or malfunctioning lifts, but reporting the problem and finding out what happened can be unclear. Repeated reports can make it difficult for staff to see what is pending and for the hostel to maintain a consistent history of recurring issues.

HostelFix aims to provide a structured process to report a problem against a specific hostel location, track its progress, and record its resolution. Staff and administrators are intended to use the same system to manage reports and review maintenance and housekeeping activity.

## Milestone scope

### MS-1 and MS-2: problem definition and system design

The earlier milestones established the project problem, requirements, user roles, proposed workflows, and system design. Those design decisions remain the basis for the implementation. Refer to the project design document, if present in the repository, for the full specification.

### MS-3: backend and database foundation

The current MS-3 work focuses on the backend and database rather than a complete frontend or fully integrated authentication and AI system. It includes:

- FastAPI application and versioned REST endpoints.
- SQLAlchemy models for the core hostel, location, category, asset, complaint, status/update, confirmation, feedback, and notification data.
- Alembic-managed database migrations.
- MySQL database configuration and Docker Compose setup.
- Reproducible synthetic seed data for development and demonstrations.
- Request validation, consistent error responses, pagination, and access/privacy checks in implemented API flows.
- Automated tests for implemented behaviour.

Authentication, the frontend, and the SmartReport AI workflow are part of the wider system vision and should be treated as future/integration work unless a corresponding implementation is present in the current branch.

## System vision and key features

The overall HostelFix design includes the following capabilities. Not every item is implemented in MS-3.

- **Structured reporting:** choose a hostel, floor, wing, area, category, and problem type.
- **Tracked complaint lifecycle:** give each complaint an identifier and record its status changes.
- **Progress history:** retain updates so the handling of a complaint can be followed.
- **Resolution confirmation:** allow the original reporter to confirm a fix or provide feedback according to the designed workflow.
- **Community issues:** provide a privacy-conscious view of issues and a possible “Me too” mechanism to reduce duplicate reporting.
- **Notifications:** notify users about relevant changes.
- **Staff workflow:** allow staff to view and update complaints within their assigned responsibilities.
- **Administrator analytics:** support review of complaint volume, status, and overdue work.
- **Institute-only access:** the design envisages access restricted to the IIT Dharwad community.

### SmartReport (planned AI feature)

The system vision includes SmartReport, which would convert a resident’s plain-language description—including English, Hinglish, or mixed language—into an editable complaint draft. The proposed flow separates drafting from complaint creation: generating a draft should not create a complaint until the user explicitly submits it.

The earlier design proposed using a backend-only Gemini API integration with schema validation, evidence checks for extracted fields, input limits, rate limiting, and graceful fallback to manual reporting. **SmartReport is not part of the core MS-3 backend scope unless its endpoints and integration are implemented in the current branch.**

## Roles and complaint lifecycle

The design identifies three principal roles:

| Role | Intended responsibilities |
|---|---|
| Student/resident | Submit complaints, view own reports and notifications, and confirm or comment on resolutions |
| Staff | Review and update complaints relevant to their assigned category |
| Administrator | Review all complaints, manage system data and accounts, and view analytics |

The proposed complaint lifecycle includes statuses such as **Submitted**, **Acknowledged**, **In Progress**, **Resolved**, **Closed**, **Rejected**, and **Reopened**. The intended design validates transitions and records the actor, timestamp, previous status, new status, and any reason or comment. Exact transition permissions and available operations depend on the implemented API and should be verified against `docs/openapi.yaml` and the application code.

HostelFix is not an emergency-response service.

## Technology stack

| Layer | Technology |
|---|---|
| Backend API | Python, FastAPI |
| API contract | OpenAPI YAML |
| ORM | SQLAlchemy |
| Database migrations | Alembic |
| Database | MySQL 8.4 (Docker image/configuration) |
| Database driver | PyMySQL |
| Configuration | Pydantic Settings / environment variables |
| Containers | Docker and Docker Compose |
| Automated tests | pytest and HTTPX |

The MS-3 backend is designed to run with the database using Docker Compose. Refer to the dependency/configuration files in the repository for the exact versions used by the current branch.

## Architecture

At a high level:

1. The client sends an HTTP request to the FastAPI application.
2. The API validates request data and invokes the relevant route and database logic.
3. SQLAlchemy maps application entities to MySQL tables.
4. Alembic manages schema changes through versioned migrations.
5. The seed script inserts deterministic synthetic development data.

The OpenAPI contract is maintained in `docs/openapi.yaml`. The API’s interactive documentation is normally available at `/docs` and `/redoc` while the application is running.

## Getting started

### Prerequisites

- Git
- Docker Desktop with Docker Compose on Windows, or Docker Engine and the Compose plugin on Linux/WSL
- A terminal such as PowerShell or WSL Ubuntu

For the Docker workflow, a separate local Python installation is generally not required to run the application.

### Run with Docker Compose

```bash
# 1. Clone the repository
git clone https://github.com/hostelfix-iitdh/hostelfix.git
cd hostelfix

# 2. Create the local environment file if the repository provides a template
cp .env.example .env

# 3. Review .env and set the values required by the current configuration.
# Never commit the real .env file.

# 4. Build and start the application and database
docker compose up --build
```

If your checkout does not contain `.env.example`, check the current README/configuration files and create only the environment variables required by the application. Do not invent credentials or commit secrets.

When the containers start successfully, open:

- API base URL: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

The application may bind to `0.0.0.0` inside the container so the host can reach it through the published port. In a browser on the same computer, use `localhost`.

### Stop the services

```bash
docker compose down
```

To remove the Compose-managed database volume as well, inspect the configured volume name and be certain you no longer need its data before running a volume-removal command. Removing volumes can permanently delete local database contents.

## Database and synthetic seed data

The development database is populated with synthetic data to make API workflows testable without using real student information. The MS-3 seed configuration is designed around:

- 2 hostels.
- 8 floors per hostel.
- 5 wings (A–E) per floor, for 80 wings in total.
- 8 area/location types, including toilet, bathroom, washing-machine area, cloth-drying area, corridor, lift lobby, drinking-water area, and room.
- 640 area locations across the 80 wings.
- 12 lifts.
- 45 seeded users.
- Approximately 40 problem types across maintenance and housekeeping categories.
- 200 synthetic complaints.

These counts describe the intended seed dataset for the MS-3 project version; the seed script and configuration in the checked-out branch are the source of truth if they differ.

The seed data is synthetic and intended for development and demonstration. Do not add real student personal information to the repository.

## REST API

The API is versioned under `/api/v1`. The implemented MS-3 routes cover the core data lookup and complaint workflows, including:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/hostels` | List hostels |
| `GET` | `/api/v1/hostels/{hostel_id}/floors` | List floors for a hostel |
| `GET` | `/api/v1/floors/{floor_id}/wings` | List wings for a floor |
| `GET` | `/api/v1/wings/{wing_id}/locations` | List locations for a wing |
| `GET` | `/api/v1/categories` | List complaint categories |
| `GET` | `/api/v1/categories/{category_id}/problem-types` | List problem types in a category |
| `GET` | `/api/v1/locations/{location_id}/assets` | List assets at a location |
| `GET` | `/api/v1/issues` | List/filter complaints |
| `POST` | `/api/v1/issues` | Create a complaint |
| `GET` | `/api/v1/issues/{issue_id}` | Retrieve complaint details |
| `PATCH` | `/api/v1/issues/{issue_id}` | Edit an eligible complaint |
| `GET` | `/api/v1/issues/{issue_id}/updates` | Retrieve complaint updates |
| `POST` | `/api/v1/issues/{issue_id}/confirmations` | Add a confirmation |
| `DELETE` | `/api/v1/issues/{issue_id}/confirmations` | Withdraw a confirmation |
| `POST` | `/api/v1/issues/{issue_id}/resolution-feedback` | Submit resolution feedback |
| `GET` | `/api/v1/staff/issues` | Retrieve the staff complaint queue |
| `PATCH` | `/api/v1/staff/issues/{issue_id}/status` | Update complaint status |
| `GET` | `/api/v1/notifications` | List notifications |
| `PATCH` | `/api/v1/notifications/{notification_id}` | Update notification state |
| `GET` | `/api/v1/admin/analytics` | Retrieve administrator analytics |

For request schemas, query parameters, response formats, and error details, use the OpenAPI file and the running Swagger UI. Availability and authorization behaviour should be confirmed against the current implementation and tests.

### API conventions

- Request bodies are validated by the API.
- List endpoints use pagination where supported; the standard response includes pagination information such as `page`, `size`, and `total`.
- Errors use a consistent response structure.
- Duplicate active complaint submissions are checked by the current implementation; an identical recent duplicate may return `409 Conflict`.
- Invalid edits or invalid status transitions may return validation or conflict responses rather than silently changing data.

## Testing and validation

Run tests from the project root in the environment configured by the repository.

### With Docker Compose

If the API service is named `api` in `docker-compose.yml`, run:

```bash
docker compose exec api python -m pytest -q
```

Check the actual service name in `docker-compose.yml` if this command reports that no `api` service exists.

### With a local Python virtual environment

Use the Python version and dependencies specified by the repository. A typical workflow is:

```bash
python -m venv .venv
source .venv/bin/activate       # Linux / WSL
python -m pip install -r requirements.txt
python -m pytest -q
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

The exact test count may change as the project evolves. A passing test suite does not replace checking the application against the OpenAPI contract or manually exercising the running service.

## Security and privacy

The design aims to protect complaint and resident information. The MS-3 implementation includes privacy-aware response handling and validation in the complaint workflows. The wider design includes these requirements:

- Validate request data on the server.
- Enforce ownership and role checks on protected operations.
- Do not expose reporter names, email addresses, student IDs, or room labels in public/community complaint responses.
- Keep credentials and API keys in environment variables or a local, ignored `.env` file.
- Never commit `.env`, access tokens, passwords, or real student data.
- Use synthetic data for development and demonstrations.

Authentication and institute-only access must be fully integrated and verified before treating the application as production-ready. Do not assume a design requirement is enforced unless it exists in the current code and is covered by tests.

## Project structure

The following is a representative structure. File names may vary slightly by branch; inspect the repository for the exact layout.

```text
hostelfix/
├── app/
│   ├── core/              # Shared application logic and configuration
│   ├── db/                # Database setup and sessions
│   ├── models/            # SQLAlchemy models
│   ├── routers/           # FastAPI route handlers
│   ├── schemas/           # Request and response schemas
│   ├── main.py            # FastAPI application entry point
│   └── seed.py            # Synthetic seed data
├── alembic/               # Versioned database migrations
├── config/                # Hostel layout and related configuration
├── docs/
│   └── openapi.yaml       # OpenAPI specification
├── tests/                 # Automated tests
├── AI_USAGE.md            # AI assistance disclosure
├── DEPENDENCIES.md        # Dependency notes, if present
├── Dockerfile
├── docker-compose.yml
├── .env.example           # Environment template, if present
├── requirements.txt
└── README.md
```

## Team workflow and contributions

The repository's `main` branch is protected. Follow the active GitHub ruleset when contributing.

1. Fetch the latest repository state.
2. Create a branch named `feature/<topic>` or `fix/<topic>`.
3. Make changes related to your assigned work.
4. Run relevant tests and inspect the diff.
5. Commit using your own GitHub account so the history accurately reflects your contribution.
6. Push your branch and open a pull request into `main`.
7. Request another team member to review the PR and address feedback before merging, according to the repository's rules.

Example:

```bash
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c feature/short-description

# Make and test your actual changes
git status
git diff
git add <specific-files>
git commit -m "Describe the change"
git push -u origin feature/short-description
```

Do not commit generated virtual environments, cache files, database files, `.env`, or secrets. Avoid broad `git add .` unless you have carefully inspected `git status`.

## AI usage

AI assistance used during development should be disclosed in [`AI_USAGE.md`](AI_USAGE.md), if that file is present in the repository. Team members should review, understand, test, and take responsibility for all submitted code and documentation.

## Acknowledgements

Built as a course project at IIT Dharwad. Development uses synthetic data and is intended for academic demonstration.
