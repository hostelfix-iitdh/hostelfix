# HostelFix: AI-Powered Hostel Maintenance and Housekeeping Portal

HostelFix is a multi-page web application backed by a MySQL database and a documented REST API. Hostel residents report maintenance and housekeeping problems with their exact location, track them until they are fixed, and confirm the fix. Staff and administrators manage and review those reports in one place.

> **Design document:** see [`docs/HostelFix_Design_Document.pdf`](docs/HostelFix_Design_Document.pdf) for the full specification (adjust the path if you store it elsewhere).

<<<<<<< HEAD
=======
---

## Table of Contents
>>>>>>> 3c29450 (Milestone-1)

- [Team](#team)
- [Problem Statement](#problem-statement)
- [Key Features](#key-features)
- [SmartReport (AI Feature)](#smartreport-ai-feature)
- [User Roles](#user-roles)
- [Complaint Lifecycle](#complaint-lifecycle)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Dataset and Seed Data](#dataset-and-seed-data)
- [API Documentation](#api-documentation)
- [Running Tests](#running-tests)
- [Security and Privacy](#security-and-privacy)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [AI Usage](#ai-usage)

---

## Team

| No. | Name | Roll Number | GitHub |
|-----|------|-------------|--------|
| 1 | Narasimha Reddy Boggula | CS26MT002 | [@Narasimha013](https://github.com/Narasimha013) |
| 2 | Aakash Saran V | CS26MT018 | [@AakashSaran018](https://github.com/AakashSaran018) |
| 3 | Suru Rakesh | CS26MT022 | [@cs26mt022](https://github.com/cs26mt022) |

Repository: <https://github.com/hostelfix-iitdh/hostelfix>

---

## Problem Statement

In a hostel, a resident who notices a dirty corridor, an overflowing dustbin, a broken light or a stopped lift usually has to find out whom to contact, pass on the details, and later ask again to learn whether anything was done. There is typically no single record showing whether the problem was received, who is handling it, or whether other residents face the same problem.

As a result, the same issue is reported repeatedly, staff have no consolidated view of what is pending, and the hostel has no reliable history of recurring problems.

HostelFix gives residents one place to **report** a problem with its exact location, **track** it until fixed, and **confirm** the fix, and gives staff and administrators one place to **manage and review** reports.

---

## Key Features

- **Structured reporting:** cascading selection of hostel, floor, wing and area, plus category and problem type.
- **SmartReport:** an AI feature that turns a plain-language description (English, Hinglish or mixed) into an editable draft complaint.
- **Tracked lifecycle:** every complaint gets an ID and moves through a validated status model with a full audit trail.
- **In-app notifications:** residents are notified whenever the status of their complaint changes.
- **Community Issues:** a privacy-safe, anonymous list of complaints, where residents can add **"Me too"** instead of filing duplicates.
- **Resolution confirmation:** the original reporter confirms the fix or requests reopening.
- **Role-based dashboards:** staff see only their assigned category; administrators get analytics, overdue tracking and account management.
- **Institute-only access:** students must use a verified `iitdh.ac.in` email or IIT Dharwad Google sign-in.

### Pages

The application has nine pages:

| Page | Available to |
|------|--------------|
| Login and Registration | Everyone |
| Dashboard | Students |
| Report an Issue | Students |
| Community Issues | Signed-in users |
| Issue Details | Signed-in users (role-based content) |
| My Reports | Students |
| Profile | Signed-in users |
| Staff Dashboard | Staff, administrators |
| Admin Dashboard | Administrators |

---

## SmartReport (AI Feature)

SmartReport lets a student describe a problem in natural language and returns a structured, editable draft: hostel, floor, wing, area, asset, category, problem type, short description, missing fields, and whether clarification is needed. Each suggested field comes with the exact supporting words from the student's text; fields not directly supported are highlighted as **inferred**.

**Example**

> "The lift in Hostel 1, Wing B, Floor 4 is not working."

| Field | Suggested value | Shown as |
|-------|-----------------|----------|
| Hostel / Floor / Wing | Hostel 1 / Floor 4 / Wing B | Stated |
| Area | Lift Lobby | Inferred |
| Asset | Not suggested (student chooses the lift) | Missing |
| Category | Maintenance | Inferred |
| Problem type | Lift not working | Stated |

**How it is built**

- **Model:** Google Gemini API, `gemini-2.5-flash-lite` (configurable via environment variable), called **only from the backend** behind a thin provider interface.
- **Two separate endpoints:** `POST /api/v1/issues/draft` returns a draft only and never creates a complaint; `POST /api/v1/issues` creates a complaint after explicit submission.
- **Schema-validated output:** every value is validated against real locations, assets, categories and problem types, and anything that does not match is dropped.
- **Evidence check:** for location fields, the supporting span must appear in the student's text and contain the value or a configured alias (e.g. "H1"), so the model cannot invent a location.
- **Privacy:** only the typed text and the list of valid option names are sent. Emails, phone numbers and roll numbers are stripped first. No account identifiers are ever sent.
- **Guardrails:** input length limit (500 characters by default), rate limit (10 drafts per user per day by default), and student text is treated as untrusted data, not instructions.
- **Graceful failure:** if the AI service is slow, unavailable, over quota or returns invalid output, the manual form remains fully usable.

---

## User Roles

| Capability | Student | Staff | Administrator |
|------------|:-------:|:-----:|:-------------:|
| Submit a complaint (manual or SmartReport) | Yes | No | No |
| Browse Community Issues | Yes | Yes | Yes |
| Add or withdraw "Me too" | Yes | No | No |
| View own reports and notifications | Yes | No | No |
| See who reported a complaint | Own only | No | Yes |
| See the room label | Own only | Assigned category | Yes |
| Confirm resolution or request reopening | Own only | No | No |
| Update status and add progress notes | No | Assigned category | Yes (any) |
| Manage accounts, roles, locations, categories, assets | No | No | Yes |
| View analytics | No | No | Yes |

Permissions are enforced by the backend on every protected endpoint. A user cannot give themselves a staff or administrator role.

---

## Complaint Lifecycle

| From | To | Who | Required |
|------|----|-----|----------|
| (new) | Submitted | System | Valid complaint |
| Submitted | Acknowledged | Staff of category / admin | None |
| Submitted or Acknowledged | Rejected | Staff of category / admin | Reason |
| Acknowledged | In Progress | Staff of category / admin | None |
| In Progress | Resolved | Staff of category / admin | Resolution note |
| Resolved | Closed | Original reporter | Optional comment |
| Resolved | Closed | System | 7 days with no response (configurable) |
| Resolved | Reopened | Original reporter | Comment |
| Reopened | In Progress | Staff of category / admin | None |

- **Closed** and **Rejected** are final. A Closed complaint cannot be reopened; the student files a new one.
- Every change records the actor, actor role, timestamp, previous and new status, reason and comment.
- Each category has an administrator-set target resolution time. A complaint is **overdue** when its due date has passed and it is not Resolved, Closed or Rejected (calculated, not stored).
- The backend rejects every transition not listed above.

> HostelFix is not an emergency-response service.

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend | Python, FastAPI; OpenAPI 3.x specification as a YAML file |
| Database | MySQL 8, SQLAlchemy ORM, Alembic migrations |
| Frontend | HTML, CSS and JavaScript, served by the backend container |
| AI | Gemini API (`gemini-2.5-flash-lite`), backend only |
| Authentication | Email + password (Argon2), email verification, password reset, Google Sign-In (ID token verified on the backend), server-side session cookies |
| Email | SMTP via environment variables; log output in demo mode |
| Testing | pytest, pytest-cov, Playwright (end-to-end) |
| CI | GitHub Actions: Ruff, all tests and coverage, MySQL service container |
| Packaging | Docker and Docker Compose |

The whole stack runs in two containers: a MySQL 8 container and an application container serving both the FastAPI backend and the frontend files.

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose (nothing else is required)

### Run the project

```bash
# 1. Clone the repository
git clone https://github.com/hostelfix-iitdh/hostelfix.git
cd hostelfix

# 2. Create your environment file
cp .env.example .env
# then edit .env and fill in the values (see "Environment Variables")

# 3. Start everything
docker compose up
```

`docker compose up` starts the database, applies the Alembic migrations, loads the seed data, and starts the application. Once it is running, open the URL printed in the logs (typically <http://localhost:8000>).

In demo mode, verification and password-reset emails are written to the application log if no SMTP account is configured, so you can copy the links from the logs.

### Seeded demo accounts

The seed script creates 40 students, 4 staff (2 per category) and 1 administrator with placeholder emails. All seeded accounts are marked as verified. See `config/` and the seed script for the exact credentials used in development.

---

## Environment Variables

Copy `.env.example` to `.env`. Never commit `.env`. Typical variables:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` / MySQL credentials | Database connection |
| `SECRET_KEY` | Session signing |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | First administrator, created at first start |
| `GEMINI_API_KEY` | Gemini API key (backend only) |
| `GEMINI_MODEL` | Model name (default `gemini-2.5-flash-lite`) |
| `GOOGLE_CLIENT_ID` | Google Sign-In audience for ID token verification |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | Outgoing email (optional in demo mode) |
| `SMARTREPORT_MAX_CHARS` | Input length limit (default 500) |
| `SMARTREPORT_DAILY_LIMIT` | Draft requests per user per day (default 10) |
| `AUTO_CLOSE_DAYS` | Days before a Resolved complaint is auto-closed (default 7) |

> The authoritative list is in `.env.example`. Update this table if variable names differ.

API keys and credentials belong only in GitHub Secrets and the git-ignored `.env` file.

---

## Dataset and Seed Data

HostelFix uses a **synthetic dataset** built by the team. No external dataset is used and no real student data is involved.

- **Layout:** 2 hostels, 8 floors each, 5 wings per floor (80 wings total), defined in `config/hostel_layout.yaml` so it can be corrected without code changes.
- **Areas per wing:** Toilet, Bathroom, Washing Machine Area, Cloth Drying Area, Corridor, Lift Lobby, Drinking Water Area, Room.
- **Assets:** six lifts per hostel in three lobbies (Lift 1 near the entrance/stairs, Lifts 2 and 3 for wings B and C, Lifts 4 to 6 for the middle lobby serving wings D and E), plus optional water dispensers. Lift-to-lobby links are read from configuration.
- **Categories:** Maintenance and Housekeeping, with about 40 problem types, each list including "Other".
- **Complaints:** about 200 synthetic complaints over the previous 60 days with varied statuses, plus updates, "Me too" records, resolution feedback and notifications.
- **Determinism:** the seed script uses a fixed random seed, so every run produces the same data. Individual rooms are not seeded; students enter an optional room label instead.

The seed script runs automatically with `docker compose up`, after the migrations.

---

## API Documentation

The REST API is documented in an OpenAPI 3.x YAML specification delivered with the repository. When the application is running, FastAPI's interactive docs are typically available at:

- Swagger UI: `/docs`
- ReDoc: `/redoc`

Key endpoints:

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/issues/draft` | SmartReport draft (never creates a complaint) |
| `POST /api/v1/issues` | Create a complaint after explicit submission |

---

## Running Tests

All model calls are mocked in unit and integration tests, so tests never depend on an external service or spend API quota.

```bash
# Unit and integration tests with coverage
pytest --cov

# Linting
ruff check .

# End-to-end tests
playwright install
pytest tests/e2e
```

Adjust commands to match your project layout. In CI, GitHub Actions runs Ruff, all tests and coverage on every push and pull request, using a MySQL service container.

### SmartReport evaluation

A separate evaluation set of 40 manually reviewed inputs (including Hinglish, typos, very short inputs, partial-location traps and prompt-injection attempts) is run against the real model. For each input we record JSON validity, field matches, clarification behaviour, unsupported values, response time and failures. A small user study (five volunteers, six scenarios each, manual form vs SmartReport) measures whether SmartReport actually saves time. Results are reported honestly in the final report.

---

## Security and Privacy

- **Exact college-domain rule:** student emails are lower-cased, split at the last `@`, and accepted only if the domain is exactly `iitdh.ac.in`. Look-alikes such as `x@notiitdh.ac.in` or `x@mail.iitdh.ac.in` are rejected. Checked on the backend.
- **Email verification:** single-use token (stored hashed, valid 24 hours); unverified accounts cannot sign in.
- **Password reset:** single-use token (stored hashed, valid 30 minutes); identical response whether or not the account exists; ends existing sessions.
- **Google sign-in:** the backend verifies signature, audience, expiry, `email_verified`, and `hd == iitdh.ac.in`.
- **Passwords:** salted Argon2 (or bcrypt) hashes, never logged or returned by any API.
- **Sessions:** HttpOnly, SameSite cookies with expiry and CSRF protection.
- **Authorization:** roles stored server-side; ownership checked on every request; IDs in URLs are never trusted on their own.
- **Privacy:** community and public responses never include reporter name, email, student ID, internal ID or the room label. Only administrators can see who reported a complaint. Deleting an account removes personal data; complaint history is kept anonymised.
- **Input safety:** ORM/parameterised queries only, server-side validation and length limits, and rate limiting on login, registration, verification, password reset and draft requests.
- **Review:** the application will be checked against the OWASP Top 10 and results listed in the final report.

---

## Project Structure

> Illustrative; update to match the actual repository layout.

```
hostelfix/
├── app/                    # FastAPI backend (routers, models, services)
├── frontend/               # HTML, CSS, JavaScript
├── alembic/                # Database migrations
├── config/                 # hostel_layout.yaml, categories, lift-to-lobby links
├── seed/                   # Seed script (Faker + complaint templates)
├── tests/                  # pytest unit/integration and Playwright e2e tests
├── docs/                   # Design document and OpenAPI YAML
├── .github/                # CI workflows and pull request template
├── AI_USAGE.md
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

---

## Contributing

The `main` branch is protected by the **"Protect main"** ruleset:

- Changes go in **only through pull requests** with at least one approval from another team member.
- Force pushes and branch deletion are blocked.

Workflow:

1. Create a branch named `feature/<topic>` or `fix/<topic>`.
2. Commit under your own GitHub account so history shows individual contribution.
3. Open a pull request using the provided template and request a review.
4. Make sure Ruff, tests and coverage pass in CI before merging.

Never commit API keys or credentials. Use GitHub Secrets and the git-ignored `.env` file.

---

## AI Usage

AI assistance used during the development of this project is documented in [`AI_USAGE.md`](AI_USAGE.md).

---

## Acknowledgements

Built as a course project at IIT Dharwad. The dataset is entirely synthetic and no real student data is used.
