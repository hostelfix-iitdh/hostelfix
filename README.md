# HostelFix

**Report, track and resolve hostel maintenance and housekeeping problems at IIT Dharwad.**

[![CI](https://github.com/hostelfix-iitdh/hostelfix/actions/workflows/ci.yml/badge.svg)](https://github.com/hostelfix-iitdh/hostelfix/actions/workflows/ci.yml)

HostelFix is a multi-page web application with a FastAPI backend, a MySQL 8 database and a documented REST API. Students report a problem together with its exact location, follow it until it is fixed, and confirm the fix. Staff work through a queue for their own category. Administrators see statistics and manage the service. An AI feature, **SmartReport**, turns a plain-language description (and an optional photo) into an editable draft of the complaint form.

This project was built for the *Course Project 2026: Build, Test and Ship an AI-Enabled Web Application* (Theme 3, campus services portal).

| | |
|---|---|
| Repository | https://github.com/hostelfix-iitdh/hostelfix |
| Team | Narasimha Reddy Boggula (CS26MT002), Aakash Saran V (CS26MT018), Suru Rakesh (CS26MT022) |
| Backend | Python 3.13, FastAPI, SQLAlchemy, Alembic |
| Database | MySQL 8.4 |
| Frontend | Plain HTML, CSS and JavaScript served by Nginx |
| AI | Gemini API, called from the server only |
| Packaging | Docker Compose (three containers) |

---

## Contents

1. [Features](#features)
2. [Quick start](#quick-start)
3. [Configuration](#configuration)
4. [Sign-in and demo accounts](#sign-in-and-demo-accounts)
5. [SmartReport (AI)](#smartreport-ai)
6. [Complaint lifecycle](#complaint-lifecycle)
7. [Architecture](#architecture)
8. [API](#api)
9. [Tests and quality checks](#tests-and-quality-checks)
10. [Project layout](#project-layout)
11. [Security and privacy](#security-and-privacy)
12. [Known limitations](#known-limitations)
13. [Troubleshooting](#troubleshooting)
14. [Documents](#documents)

---

## Features

**Students**

- Sign in with their IIT Dharwad Google account (`@iitdh.ac.in` only).
- Report an issue by choosing hostel, floor, wing and area, then category and problem type. Housekeeping reports can carry a service date, and Room reports an optional room label.
- Describe the problem in one sentence and let **SmartReport** pre-fill the form.
- See similar open complaints before submitting, and press **Me too** instead of filing a duplicate.
- Follow their own reports, with a full status history and in-app notifications.
- Confirm that a fix worked, or ask for the complaint to be reopened.
- Edit or delete a complaint only while it is still `submitted`.
- Browse the **Community Issues** page, which never shows who reported what.

**Staff** (one category each: Maintenance or Housekeeping)

- A work queue limited to their own category, with filters.
- Move complaints through acknowledged, in progress and resolved, with notes. Rejecting needs a written reason.

**Administrators**

- Statistics: counts by status, category, location and problem type, overdue and reopened complaints, average resolution time.
- Create staff accounts (the administrator chooses the first password) and delete staff accounts.
- Maintain categories, problem types, locations, assets and target resolution times.

---

## Quick start

You need **Docker** (with the Compose plugin) and **Git**. Nothing else has to be installed.

```bash
git clone https://github.com/hostelfix-iitdh/hostelfix.git
cd hostelfix
docker compose up --build
```

Then open:

| What | Address |
|---|---|
| The site | http://localhost:8080 |
| API documentation (Swagger UI) | http://localhost:8000/docs |
| Alternative API docs (ReDoc) | http://localhost:8000/redoc |
| Health check | http://localhost:8000/api/v1/health |

On start-up the API container waits for MySQL, applies the Alembic migrations, loads the synthetic seed data (when `SEED_ON_STARTUP=true`) and then starts the server. The first build takes a few minutes.

Every setting has a default, so the site starts **without a `.env` file**. Google sign-in and Gemini need their own keys, described below. Without them the Google button reports that sign-in is not configured, staff and administrators can still sign in with a password, and SmartReport uses its local rules.

Useful commands:

```bash
docker compose logs -f api      # follow the API log
docker compose ps               # see running containers
docker compose down             # stop (data is kept in the mysql_data volume)
docker compose down -v          # stop AND delete the database volume
```

To rebuild the 200 synthetic demo complaints on an existing database (destructive for the local demo data):

```bash
docker compose exec api python -m app.seed --reset-demo-issues
```

---

## Configuration

Copy the example file and edit it:

```bash
cp .env.example .env        # Windows PowerShell: Copy-Item .env.example .env
```

`.env` is ignored by Git. **Never commit it, and never put keys into frontend code.** After changing it, run `docker compose down` and `docker compose up --build` so the API container picks up the new values.

| Variable | Default | Purpose |
|---|---|---|
| `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` | `hostelfix`, `hostelfix`, dev passwords | Database name and logins. Change them for any shared use. |
| `WEB_PORT`, `API_PORT`, `MYSQL_PORT` | `8080`, `8000`, `3307` | Ports on your machine. |
| `ENVIRONMENT` | `development` | Set to `production` to switch off the development login header (see below). |
| `SEED_ON_STARTUP` | `true` | Load the synthetic data when the API starts. |
| `CORS_ORIGINS` | localhost 8080, 5173, 3000 | Allowed browser origins. The first one is also used in email links. |
| `SESSION_SECRET` | placeholder | Long random string. **Must be changed** outside local use. |
| `SESSION_HOURS` | `24` | Session lifetime. |
| `COOKIE_SECURE` | `false` | Set to `true` when the site is served over HTTPS. |
| `GOOGLE_CLIENT_ID` | empty | Google OAuth Web Client ID (not a secret). |
| `GEMINI_API_KEY` | empty | Gemini key. **Secret**, used only by the API container. |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Model name. |
| `AI_TIMEOUT_SECONDS` | `30` | Time limit for the Gemini call. |
| `AI_MAX_CHARS` | `500` | Maximum SmartReport text length. |
| `AI_MAX_IMAGE_BYTES` | `5242880` | Maximum photo size (5 MB). |
| `MAIL_MODE` | `log` | `log` writes emails to the API log; any other value uses SMTP. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM` | empty / `587` | SMTP settings when mail is really sent. |

> `AI_DAILY_LIMIT` appears in the example files, but the current code always allows one Gemini draft per student per day and does not read this setting.

### Google sign-in

1. In Google Cloud Console, create an **OAuth client → Web application**.
2. Add `http://localhost:8080` as an **Authorized JavaScript origin**.
3. Put the generated Web Client ID in `.env` as `GOOGLE_CLIENT_ID`.

Do not add a client secret: HostelFix verifies the ID token on the server. The server accepts an account only if Google marks the email as verified, the hosted domain is exactly `iitdh.ac.in`, and the address passes our own exact-domain check. If the browser reports "Invalid Google ID token", check that the client ID matches the one used by the button and that the origin is registered, then rebuild. The reason for a failed check is written to `docker compose logs api` (never the token itself).

### Gemini

Create a key in Google AI Studio and put it in `.env` as `GEMINI_API_KEY`. The free tier is enough for development; quotas and model availability can change.

---

## Sign-in and demo accounts

- **Students** use **Continue with Google** with an `@iitdh.ac.in` account. A student account is created on first sign-in.
- **Staff and administrators** use the separate **Staff / Administrator login** (`/#staff-login`) with email and password.

Seeded staff and administrator accounts:

| Account | Role |
|---|---|
| `admin@iitdh.ac.in` | Administrator |
| `maintenance-staff1@iitdh.ac.in`, `maintenance-staff2@iitdh.ac.in` | Staff (Maintenance) |
| `housekeeping-staff1@iitdh.ac.in`, `housekeeping-staff2@iitdh.ac.in` | Staff (Housekeeping) |

Only **Argon2id hashes** of their passwords are stored (`app/core/role_credentials.py`); plain passwords are not in the repository. Ask the team for the demo passwords, or sign in as the administrator and create a new staff account with a password of your choosing. Seeded students (`student01@iitdh.ac.in` to `student40@iitdh.ac.in`) are Google-only identities.

**Development shortcut.** While `ENVIRONMENT` is not `production`, the API also accepts an `X-User-Id` header as a login (handy in Swagger UI and tests). In the seed data, user `1` is a student, `41` maintenance staff, `43` housekeeping staff and `45` the administrator. This shortcut must be switched off for any real deployment.

The API also contains a manual student registration route with consent and email verification (`POST /api/v1/auth/register`). It is not shown in the interface, because students are meant to use Google.

---

## SmartReport (AI)

A student types something like *"Hostel 1 floor 4 wing B lift is not working"* (English, Hinglish or a mix) and may attach a photo. SmartReport returns a draft with the hostel, floor, wing, area, category, problem type, title and description, and lists the fields it could not work out. **It never files a complaint**: the student reviews the form and submits it.

How it works:

1. `POST /api/v1/issues/draft` checks the text length (500 characters), image type and size (5 MB), and the student's daily allowance.
2. Email addresses, phone numbers and roll numbers are replaced by placeholders.
3. The server calls Gemini (30-second timeout) with the text, the list of valid options and the optional image. The reply must fit a fixed JSON schema, with the supporting words from the text for every field.
4. Our code checks the reply. A hostel, floor, wing, area or asset is kept only if the student's text really contains it, and regular expressions read obvious values straight from the text. A photo can help with category and problem type, never with the location.
5. The draft is returned to the form. The normal validation applies again on submission.

**Limits and fallbacks**

- One Gemini-powered draft per student per calendar day, stored in MySQL. After that, the same button switches to a **text-only pattern mode** and photos are refused until tomorrow. `GET /api/v1/issues/smart-report-status` tells the page which mode applies.
- At most 30 requests per hour per client address.
- If Gemini is missing, slow, out of quota or returns something unusable, the server falls back to local rules and says so. The normal form always works.

**Privacy.** Gemini receives only the redacted text, the list of options and the optional photo. It never receives names, emails, user IDs or passwords. Photos are not stored by HostelFix. The patterns that remove personal data are narrow, and a photo may still show something private, so students are asked not to include personal information.

**Evaluation.** `tests/ai_evaluation_set.json` holds 40 inputs (clear reports, shorthand such as `H2 F5 D`, Hinglish, typos, vague inputs and prompt-injection attempts). The local fallback gets 22 of 40 right and never invents a location. Results of a live Gemini run are not recorded in the repository yet.

---

## Complaint lifecycle

```
submitted ─► acknowledged ─► in_progress ─► resolved ─► closed
    │             │                ▲            │
    └──► rejected ◄┘                └─ reopened ◄┘
```

- Staff (or an administrator) move a complaint to acknowledged, in progress and resolved. `rejected` needs a written reason.
- The reporter confirms a resolved complaint (it becomes `closed`) or asks for a reopen (`reopened`, then staff continue).
- A resolved complaint with no reply is closed automatically after **7 days**, with the comment `auto-closed: no response`. A background task checks this hourly.
- `closed` and `rejected` are final. If the problem returns, file a new complaint.
- The server refuses every transition that is not allowed, and each change is stored with the actor, role and time, and creates a notification.
- Each category has a target resolution time (default 168 hours), which gives every complaint a due date. A complaint is overdue when the due date has passed and it is not closed or rejected.
- **Me too** works only on `submitted` complaints, never on Room-area complaints and never on your own.

---

## Architecture

```
 Browser ──► web (Nginx, :8080) ──/api/──► api (FastAPI, :8000) ──► db (MySQL 8.4, volume mysql_data)
    │                                          │
    └─ Google sign-in button                   ├──► Google (verifies ID tokens)
                                               ├──► Gemini API (SmartReport)
                                               └──► SMTP server, or the API log
```

- The browser talks only to Nginx, which serves the static frontend and proxies `/api/` to the API.
- Only the API container knows the database login, the Gemini key and the session secret.
- Sessions are stored in MySQL (cookie `hf_session`, stored as a hash). Write requests also need the `X-CSRF-Token` header to match the `hf_csrf` cookie.
- The schema has 16 tables, created by five Alembic migrations. See the ER diagram PDF for details.

---

## API

The prefix is `/api/v1`. Lists use `page` and `size` (1 to 50) and return `items`, `page`, `size` and `total`. Errors always look like `{"error": {"code": "...", "message": "...", "details": null}}`. Interactive documentation is at `/docs` while the stack is running.

| Area | Main endpoints | Access |
|---|---|---|
| Health | `GET /health` | Public |
| Lookups | `/hostels`, `/hostels/{id}/floors`, `/floors/{id}/wings`, `/wings/{id}/locations`, `/locations/catalog`, `/problem-types/catalog`, `/categories`, `/locations/{id}/assets` | Public |
| Complaints | `GET /issues`, `GET /issues/{id}`, `GET /issues/{id}/updates` | Public complaints only |
| Reporting | `POST /issues`, `PATCH`/`DELETE /issues/{id}`, `GET /issues/similar`, `GET /my/issues` | Signed in (edits: reporter only, while `submitted`) |
| Me too and feedback | `/issues/{id}/confirmations`, `POST /issues/{id}/resolution-feedback` | Signed in |
| SmartReport | `POST /issues/draft`, `GET /issues/smart-report-status` | Students |
| Staff | `GET /staff/issues`, `PATCH /staff/issues/{id}/status` | Staff of the category, administrators |
| Notifications | `GET /notifications`, `PATCH /notifications/{id}` | Owner |
| Profile | `GET`/`PATCH /me`, `POST /me/password` | Signed in |
| Authentication | `/auth/google`, `/auth/login`, `/auth/logout`, `/auth/csrf`, `/auth/config`, `/auth/register`, `/auth/verify`, `/auth/forgot-password`, `/auth/reset-password` | Public, rate limited |
| Administration | `GET /admin/analytics`, `GET`/`POST /admin/staff`, `DELETE /admin/staff/{id}`, and create/update routes for hostels, floors, wings, locations, categories, problem types and assets | Administrators |

> The live API has about 51 paths and 59 operations. `docs/openapi.yaml` is an older hand-written contract (32 paths, 38 operations) and is behind the code. Treat `/openapi.json` from the running API as the current description.

---

## Tests and quality checks

Run from the project root with `requirements.txt` installed (Python 3.13 recommended):

```bash
python -m pytest -m "not e2e" --cov=app --cov-report=term      # unit and integration tests
ruff check app tests                                          # lint
node --check frontend/src/app.js                              # frontend syntax check
```

- **28 unit and integration tests** run against an in-memory SQLite database in a few seconds and need no Docker. Google verification and mail sending are replaced by stubs, and no test calls Gemini. Measured coverage of `app/` is about **75%** (the CI gate is 70%).
- **3 Playwright browser tests** need the site to be running:

```bash
python -m playwright install chromium     # once
docker compose up -d --build
python -m pytest tests/e2e -m e2e -q
```

**GitHub Actions** (`.github/workflows/ci.yml`) runs on every push and pull request. Job one installs the pinned requirements, runs Ruff and the tests with the coverage gate, and uploads `coverage.xml`. Job two starts the whole stack with Docker Compose and runs the Playwright tests.

---

## Project layout

```
.
├── app/
│   ├── main.py            # app set-up, middleware, error handlers, hourly auto-close task
│   ├── core/              # settings, error format, rate limiter, problem-to-area rules
│   ├── db/session.py      # engine and session
│   ├── models/            # the 16 SQLAlchemy tables
│   ├── schemas/           # request and response models
│   ├── routers/           # auth, issues, ai, admin, locations, notifications, profile, health, demo
│   ├── services/          # security, google_auth, mailer, lifecycle, ai (Gemini)
│   └── seed.py            # deterministic synthetic data
├── alembic/versions/      # five database migrations
├── config/hostel_layout.yaml
├── frontend/              # Dockerfile, nginx.conf, src/ (index.html, app.js, styles.css)
├── tests/                 # unit, integration, e2e, AI evaluation set
├── docs/openapi.yaml
├── docker-compose.yml, Dockerfile, .env.example
└── MS-1 / MS-2 PDF documents
```

---

## Security and privacy

- **Passwords** are hashed with Argon2id and never returned or logged. Tokens (sessions, email links) are stored only as SHA-256 hashes.
- **Sessions** use an `HttpOnly`, `SameSite=Lax` cookie plus CSRF protection. Logout, password reset and account removal take effect immediately because sessions live on the server.
- **Access control** is enforced on the server: role checks on staff and admin routes, ownership checks on edits, and staff limited to their own category. Public responses never include the reporter or the room label.
- **Input**: SQLAlchemy only (no string-built SQL), Pydantic validation on every request, escaped output in the page, and image uploads limited by type and size.
- **Rate limits** apply to login, registration, verification, password reset and SmartReport.
- **Data kept**: name, college email, Google ID and the complaints a user files. All seeded data is synthetic; do not add real student data to the repository.
- **Secrets** belong in `.env` or GitHub Secrets only. `.env` is git-ignored.

Before any real deployment: set `ENVIRONMENT=production`, use a long random `SESSION_SECRET`, serve over HTTPS with `COOKIE_SECURE=true`, restrict `CORS_ORIGINS`, change the database passwords, configure SMTP, and disable the `/demo-users` endpoint.

---

## Known limitations

This list is kept honest on purpose. See the architecture report for the full discussion.

- Students cannot delete their own account in this version (`DELETE /me` returns 403). Administrators can delete staff accounts.
- The Google sign-in screen shows no consent notice yet.
- The minimum password length is 5 characters.
- `X-User-Id` works as a login unless `ENVIRONMENT=production`, and reading a private complaint honours only that header, not the session cookie.
- Rate limits are kept in memory and keyed by client address; behind Nginx all users probably share one limit.
- Creating a complaint and adding a Me too are restricted in the interface but not in the API.
- The server does not require a resolution note when a complaint is marked resolved.
- `docs/openapi.yaml` is behind the live API.
- The Playwright tests only check that the login pages render; there is no full sign-in, report and list flow yet.
- The CI test job declares a MySQL service but the tests use SQLite.
- Live Gemini evaluation results and `AI_USAGE.md` are not in the repository yet.

---

## Troubleshooting

| Problem | What to try |
|---|---|
| "Invalid Google ID token" | Check `GOOGLE_CLIENT_ID` matches the button, that `http://localhost:8080` is an authorized origin, then rebuild. Read the reason in `docker compose logs api`. |
| SmartReport says it used local text extraction | `GEMINI_API_KEY` is empty or invalid, or Gemini timed out or is out of quota. |
| SmartReport says the daily limit is reached | Each student gets one Gemini draft a day; text-only help stays available and photos return tomorrow. |
| Changes to `.env` are ignored | Run `docker compose down` then `docker compose up --build`. |
| Port already in use | Change `WEB_PORT`, `API_PORT` or `MYSQL_PORT` in `.env`. |
| Verification or reset link not received | With `MAIL_MODE=log` the link is in `docker compose logs api` (and, for registration, in the API response). |
| Start from an empty database | `docker compose down -v`, then `docker compose up --build`. This permanently deletes local data. |

---

## Documents

- `MS-1_HostelFix_Design_Document.pdf` — problem, dataset, pages, user stories, AI plan.
- `MS-2_HostelFix_ER_Diagram.pdf` — ER diagram, normal form notes and index notes.
- `MS-2_Figma_Demo.pdf` — link to the Figma prototype and its demo video.
- `docs/openapi.yaml` — OpenAPI contract (older than the code, see above).
- The architecture report describes the whole system in detail.
