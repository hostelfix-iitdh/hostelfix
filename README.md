# HostelFix — IIT Dharwad

HostelFix is a web application for reporting, tracking and managing hostel maintenance and housekeeping issues. The frontend follows the supplied **HostelFix Prototype** in Figma and the MS-1/MS-2 design documents. It includes student pages, staff workflows and an administrator overview, backed by the existing FastAPI API and MySQL database.

**Repository:** https://github.com/hostelfix-iitdh/hostelfix  
**Frontend:** HTML, CSS and JavaScript served by Nginx  
**Backend:** Python, FastAPI, SQLAlchemy and Alembic  
**Database:** MySQL 8.4  
**Local startup:** Docker Compose

## Included screens and workflows

- **Sign in:** Figma-style sign-in page, college-email/password fields and a clearly labelled development demo identity selector. Create-account, Google sign-in and password-reset open static next-milestone preview pages; these controls intentionally do not authenticate, register, or send email.
- **Dashboard:** personal report metrics, recent reports and quick actions.
- **Report an Issue:** dependent hostel → floor → wing → area selection; category/problem-type selection; room label and relevant service date; public/private visibility; editable SmartReport draft area; review-before-submit confirmation.
- **Community Issues:** public-safe issue list, search, status/hostel/floor/wing/area/category/problem filters, sorting, pagination, issue details and “Me too” confirmations for other residents’ reports only (reporters cannot confirm their own issue).
- **Issue Details:** complaint metadata, status timeline, confirmation count, reporter resolution feedback/reopen request, and authorised staff status updates with optional internal notes.
- **My Reports:** current user's reports, status filtering and pagination. The reporter can edit or delete a complaint only while it is `submitted`; once staff acknowledge it, both actions are locked.
- **Profile:** account information, sign out and account deactivation confirmation.
- **Staff Dashboard:** role/category-limited work queue and status updates.
- **Admin Dashboard:** issue metrics, status/category charts and staff-account creation.
- **Notifications:** list and mark notifications as read.

The layout is responsive and uses the Figma palette, typography, header/navigation, card shapes, field sizes, status chips and accessible focus styles. The backend remains the source of truth for validation and permissions.

## Important implementation boundaries

This is a **development/MS-4 integration build**, not a production-ready identity system:

- The existing backend uses the `X-User-Id` development identity header. The sign-in form uses seeded demo users; it does **not** authenticate the typed email/password.
- Google OAuth, email verification, password reset and self-service student registration are not configured. The UI shows static preview pages for these flows, clearly marked as planned for the next milestone.
- SmartReport's AI provider is not configured. The current button uses a small, explicit keyword rule list to suggest a likely category/problem for common faults (for example, a broken light is Maintenance, while a dirty toilet is Housekeeping). If the description is ambiguous, it leaves the classification unchanged. This is not a model/API integration and never submits automatically. The rules are in `frontend/src/app.js` under `SMART_CLASSIFICATION_RULES` so they are easy to review and extend.
- Staff creation is implemented for the development admin flow. Role/identity security must be replaced with real authentication and hardened before any deployment beyond local development.
- Schedules, SLAs, notifications delivery and advanced location/asset administration are not represented as verified institutional operations.
- Seeded data is synthetic. Do not add real student information to the repository.

## Run the project

### Prerequisites

- Docker Desktop with Docker Compose on Windows, or Docker Engine and the Compose plugin on Linux/WSL.
- Git, if cloning the repository.

### Start all services

```bash
git clone https://github.com/hostelfix-iitdh/hostelfix.git
cd hostelfix
cp .env.example .env
docker compose up --build
```

The API container waits for MySQL, runs Alembic migrations, loads synthetic seed data when `SEED_ON_STARTUP=true`, and starts FastAPI. Nginx serves the frontend and proxies `/api/` requests to the API service.

Open:

- **Frontend:** http://localhost:8080
- **API root:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

The ports can be changed using `WEB_PORT`, `API_PORT` and `MYSQL_PORT` in `.env`. Never commit `.env` or production secrets.

### Refresh the 200 synthetic demo issues

The seeded issue set uses problem-specific titles, descriptions and compatible locations. For example, **Washing machine** is a **Maintenance** problem at a washing-machine area, while **Washing machine area cleaning** is a **Housekeeping** problem at that same area. Explicitly location-bound problems are validated by the API so a mismatched area is rejected.

If a database already contains the older synthetic issues, regenerate the demo dataset from the API container:

```bash
docker compose exec api python -m app.seed --reset-demo-issues
```

This command is destructive to the local demo dataset: it recreates synthetic hostels, locations, demo accounts and the 200 sample issues. Do not run it against real or shared data. To initialize a fresh database, use `docker compose down -v` only if you are comfortable permanently deleting the local database volume.

Stop the services with:

```bash
docker compose down
```

To also delete the local database volume, first make sure its data is no longer needed; volume removal permanently deletes the local database contents.

## Development demo identities

On the sign-in screen, select one of the pre-seeded demo identities:

| Demo role | User ID | Purpose |
|---|---:|---|
| Student | `1` | Dashboard, reporting, community, My Reports, profile |
| Maintenance staff | `41` | Maintenance work queue and staff actions |
| Housekeeping staff | `43` | Housekeeping work queue and staff actions |
| Administrator | `45` | Admin analytics and staff-account creation |

These IDs correspond to the deterministic seed order in the current seed script. If the seed logic changes, confirm the user IDs in the database. The demo password displayed in the UI is illustrative only; the current API does not verify it.

## Tests and quality checks

Run from the project root in an environment with `requirements.txt` installed:

```bash
python -m pytest -q
python -m pytest --cov=app --cov-report=term --cov-report=xml:coverage.xml --cov-fail-under=65 -q
node --check frontend/src/app.js
```

The tests use an isolated in-memory SQLite database. The current suite has 11 tests and measured about 66% application coverage in the development environment. It includes issue creation/listing, reporter edit/delete, and the rule that acknowledged complaints cannot be edited or deleted. These tests do not replace a full Docker/MySQL smoke test. GitHub Actions runs Ruff checks and pytest coverage on pushes and pull requests; check the Actions run for the authoritative CI result.

## REST API highlights

The API prefix is `/api/v1`. Interactive request/response documentation is available at `/docs` while the app is running. The maintained contract is `docs/openapi.yaml`.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/hostels`, `/hostels/{id}/floors`, `/floors/{id}/wings`, `/wings/{id}/locations` | Dynamic location hierarchy |
| `GET` | `/locations/catalog`, `/problem-types/catalog` | UI-friendly location/problem catalogs |
| `GET` | `/categories`, `/categories/{id}/problem-types`, `/locations/{id}/assets` | Category, problem and asset lookup |
| `GET` | `/issues` | Public issue listing and filtering |
| `POST` | `/issues` | Submit a report |
| `GET` | `/issues/{id}` and `/issues/{id}/updates` | Issue details and timeline |
| `GET` | `/my/issues`, `/me` | Current demo user's reports/profile |
| `PATCH` | `/issues/{id}` | Edit a report only while its status is `submitted` |
| `DELETE` | `/issues/{id}` | Delete a report only while its status is `submitted` |
| `GET`, `POST`, `DELETE` | `/issues/{id}/confirmations` | Read count/add/remove “Me too” confirmation |
| `POST` | `/issues/{id}/resolution-feedback` | Confirm resolution or request reopening |
| `GET` | `/staff/issues` | Authorised staff queue |
| `PATCH` | `/staff/issues/{id}/status` | Status/progress update |
| `GET`, `PATCH` | `/notifications`, `/notifications/{id}` | Notifications and read state |
| `GET` | `/admin/analytics` | Administrator metrics |
| `POST` | `/admin/staff` | Create a staff account in the development flow |
| `GET`, `DELETE` | `/me` | Read/deactivate the current demo profile |

## Project data model

The synthetic seed represents two hostels, eight floors per hostel, five wings (A–E) per floor, eight area types per wing, two maintenance/housekeeping categories, configurable problem types and assets, demo users, complaints, status updates, confirmations, feedback and notifications. Exact seed values are defined in `app/seed.py`.

## Security note

Do not deploy this development build publicly as-is. Replace `X-User-Id` with verified server-side authentication, configure approved college-domain checks and OAuth, protect admin/staff routes with real role claims, configure CSRF/session protections as appropriate, and perform a privacy/security review before using real student data.
