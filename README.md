# HostelFix

**AI-powered hostel maintenance and housekeeping portal**

HostelFix lets hostel residents report maintenance and housekeeping problems with their exact location, track them until they are fixed, and confirm that the fix worked. Authorized staff manage and resolve the reports, and administrators review overdue complaints and analytics.

This is a team project for *Course Project 2026: Build, Test and Ship an AI-Enabled Web Application* (Theme 3: Campus services portal), IIT Dharwad.

> **Project status: Milestone 1 (design).** The problem statement and design are complete. Application code is added from Milestone 3 onwards. Sections marked **(Planned)** describe what the repository will contain and are not runnable yet.

## Problem

In a hostel, a resident who notices a problem (a dirty corridor, a broken light, a lift that has stopped working) usually has to find out whom to contact, pass on the details, and later ask again whether anything was done. There is no single record showing whether the problem was received, who is handling it, or whether others face the same problem. HostelFix gives residents one place to report and track problems, and gives staff and administrators one place to manage and review them.

## Features

- **Exact location reporting:** cascading selection of hostel, floor, wing and area (Toilet, Bathroom, Washing Machine Area, Cloth Drying Area, Corridor, Lift Lobby, Drinking Water Area, Room), plus category and problem type.
- **SmartReport (AI):** a student describes a problem in plain language and gets an editable draft complaint. A complaint is created only when the student reviews and submits it. If the AI service is unavailable, the manual form still works.
- **Community Issues:** a signed-in list of complaints that never shows who reported them. Residents add a "Me too" instead of filing duplicates, and see similar open complaints before submitting.
- **Tracked lifecycle:** Submitted, Acknowledged, In Progress, Resolved, Closed, Reopened, Rejected and Timeout. The original reporter confirms the fix (Closed) or asks for reopening (Reopened). If the reporter does not respond within 7 days (configurable), a Resolved complaint moves to Timeout instead of Closed.
- **Role-based access:** students, staff (assigned to Maintenance or Housekeeping) and administrators, enforced by the backend.
- **Analytics:** complaint counts by category, location and status, overdue complaints, and average resolution time for administrators.
- **Privacy:** reporter identity is visible only to administrators, and only the typed complaint text is sent to the AI model, with emails and phone numbers removed first.

## Pages

Login and Registration, Dashboard, Report an Issue, Community Issues, Issue Details, My Reports, Profile, Staff Dashboard and Admin Dashboard.

## Roles

| Role | What they can do |
|---|---|
| Student | Report complaints, add "Me too", track own reports, confirm or reopen a resolution, browse Community Issues |
| Staff | Browse Community Issues, update status and add notes for the assigned category only (Maintenance or Housekeeping) |
| Administrator | Everything staff can do across all categories, plus manage accounts, locations, categories and assets, view analytics, and see who reported a complaint |

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Python, FastAPI, OpenAPI 3.x specification (YAML) |
| Database | MySQL 8, SQLAlchemy ORM, Alembic migrations |
| Frontend | HTML, CSS and JavaScript, served by the backend container |
| AI | Gemini API, called from the backend only |
| Testing | pytest and pytest-cov, Playwright for end-to-end tests |
| CI | GitHub Actions with Ruff linting, tests and coverage |
| Packaging | Docker and Docker Compose |

## Getting started (Planned)

Prerequisites: Docker and Docker Compose. Nothing else needs to be installed.

```bash
git clone https://github.com/cs26mt022/hostelfix.git
cd hostelfix
cp .env.example .env     # then fill in the values described below
docker compose up
```

`docker compose up` starts the MySQL container and the application container, applies the database migrations, loads the seed data and starts the app. The site address and the demo accounts will be listed here once the application is available.

## Configuration (Planned)

Settings come from environment variables. The final list will be in `.env.example`; the names below may change. Never commit your real `.env` file or any API key.

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Gemini API key, used by the backend only |
| `MYSQL_*` | Database name, user and password |
| `SECRET_KEY` | Signs session cookies |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Credentials for the first administrator account, created at first start |
| `ALLOWED_EMAIL_DOMAIN` | Accepted sign-up domain (`iitdh.ac.in`) |
| `AI_MAX_INPUT_CHARS` | Maximum SmartReport input length (default 500) |
| `AI_RATE_LIMIT_PER_HOUR` | Draft requests per user per hour (default 10) |
| `TIMEOUT_DAYS` | Days without a reporter response before a Resolved complaint moves to Timeout (default 7) |

## Seed data (Planned)

The dataset is synthetic. A Python seed script (Faker plus hand-written complaint templates, fixed random seed) creates the hostel layout (2 hostels, 8 floors each, 5 wings A to E per floor), categories and about 40 problem types, about 10 students, 2 staff and 1 administrator, and about 50 complaints over the previous 30 days with varied statuses. No real student data is used.

## Running the tests (Planned)

```bash
pytest --cov          # unit and integration tests; AI calls are mocked
ruff check .          # linting
```

End-to-end tests run with Playwright. The same checks run on every push and pull request through GitHub Actions. Coverage targets are 60% by Milestone 4 and 70% by Milestone 5.

## API documentation (Planned)

The full API is described in `openapi.yaml` and can be viewed in the interactive documentation that FastAPI serves with the running app.

## Planned repository structure

```
backend/          FastAPI application
frontend/         HTML, CSS and JavaScript
database/         Alembic migrations and seed script
tests/            Unit, integration and end-to-end tests
docs/             Design and report documents
docker-compose.yml
openapi.yaml
AI_USAGE.md       AI tools used, for what, and one example of wrong output
.env.example
```

## Team

| No. | Name | Roll number | GitHub |
|---|---|---|---|
| 1 | Narasimha Reddy Boggula | CS26MT002 | [Narasimha013](https://github.com/Narasimha013) |
| 2 | Aakash Saran V | CS26MT018 | [AakashSaran018](https://github.com/AakashSaran018) |
| 3 | Suru Rakesh | CS26MT022 | [cs26mt022](https://github.com/cs26mt022) |

## Contributing

Direct pushes to `main` are blocked. Every change goes through a pull request that another team member reviews and that passes CI.
