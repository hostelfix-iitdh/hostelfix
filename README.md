# HostelFix — IIT Dharwad

HostelFix is a web application for reporting, tracking and managing hostel maintenance and housekeeping issues. The frontend follows the supplied **HostelFix Prototype** in Figma and the MS-1/MS-2 design documents. It includes student pages, staff workflows and an administrator overview, backed by the existing FastAPI API and MySQL database.

**Repository:** https://github.com/hostelfix-iitdh/hostelfix  
**Frontend:** HTML, CSS and JavaScript served by Nginx  
**Backend:** Python, FastAPI, SQLAlchemy and Alembic  
**Database:** MySQL 8.4  
**Local startup:** Docker Compose

## Included screens and workflows

- **Sign in:** IIT Dharwad email/password authentication, student registration with email verification, password reset, profile management, account deletion/anonymisation, and Google Identity Services sign-in restricted to verified iitdh.ac.in accounts.
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

This MS-5 build uses the real authentication and AI paths required for the milestone:

- Server-side session cookies with CSRF protection are used for authenticated browser sessions.
- Manual registration/login is restricted to `@iitdh.ac.in` accounts. Registration requires consent and email verification.
- Google Identity Services is supported, and the backend verifies the Google ID token before accepting the login. Only verified Google accounts with the `iitdh.ac.in` hosted domain are accepted.
- Passwords are stored as Argon2 hashes; plaintext passwords are never stored or returned.
- SmartReport uses the Gemini Developer API when `GEMINI_API_KEY` is configured. The model receives only the complaint text and optional uploaded image needed for classification.
- SmartReport can classify image evidence such as a damaged washing machine or faulty/stuck lift and proposes a category/problem type. The user must review the draft before submission.
- If Gemini is unavailable, times out or reaches the application rate limit, the manual complaint form remains usable.
- Staff/admin workflows use the same authenticated session mechanism.
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

These IDs correspond to the deterministic seed order in the current seed script. If the seed logic changes, confirm the user IDs in the database. Student accounts are Google-only for sign-in. Fixed staff/administrator development credentials are stored in `app/core/role_credentials.py` and are hashed into the database by the seed script.

For the local MS-5 demo, the fixed manual-login accounts are:
- `admin@iitdh.ac.in` — administrator
- `maintenance-staff1@iitdh.ac.in` — staff
- `maintenance-staff2@iitdh.ac.in` — staff
- `housekeeping-staff1@iitdh.ac.in` — staff
- `housekeeping-staff2@iitdh.ac.in` — staff

Only Argon2id password hashes are stored in `app/core/role_credentials.py`; plaintext passwords are never stored in the repository. The fixed demo passwords from the previous MS5 package remain valid because only their stored representation was changed.

## Tests and quality checks

Run from the project root in an environment with `requirements.txt` installed:

```bash
python -m pytest -q
python -m pytest --cov=app --cov-report=term --cov-report=xml:coverage.xml --cov-fail-under=65 -q
node --check frontend/src/app.js
```

The tests use an isolated in-memory SQLite database. The current suite has 20 tests and measured about 66% application coverage in the development environment. It includes issue creation/listing, reporter edit/delete, and the rule that acknowledged complaints cannot be edited or deleted. These tests do not replace a full Docker/MySQL smoke test. GitHub Actions runs Ruff checks and pytest coverage on pushes and pull requests; check the Actions run for the authoritative CI result.

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

For deployment, set a strong `SESSION_SECRET`, use HTTPS with `COOKIE_SECURE=true`, configure the Google Web Client ID, configure SMTP if real email delivery is required, and keep the Gemini API key only in environment variables/GitHub Secrets.

## MS-5 Authentication and SmartReport

### Authentication
- Students use Google Sign-In only. Google accounts must use the exact `@iitdh.ac.in` domain. Staff/administrator accounts use the separate manual email/password login. Student registration/password login is not exposed in the UI.
- Sessions use an HttpOnly, SameSite cookie plus a CSRF token for state-changing API requests.
- Account deletion anonymises the account while retaining complaint history.

### Demo credentials
Student accounts are Google-only for sign-in. Fixed staff/administrator development credentials are stored in `app/core/role_credentials.py` and are hashed into the database by the seed script.

For the local MS-5 demo, the fixed manual-login accounts are:
- `admin@iitdh.ac.in` — administrator
- `maintenance-staff1@iitdh.ac.in` — staff
- `maintenance-staff2@iitdh.ac.in` — staff
- `housekeeping-staff1@iitdh.ac.in` — staff
- `housekeeping-staff2@iitdh.ac.in` — staff

Only Argon2id password hashes are stored in `app/core/role_credentials.py`; plaintext passwords are never stored in the repository. The fixed demo passwords from the previous MS5 package remain valid because only their stored representation was changed.
- `student01@iitdh.ac.in` through `student40@iitdh.ac.in` are Google-only demo student identities.

### Google setup
Create a Google OAuth Web Client ID for `http://localhost:8080` and put it in `GOOGLE_CLIENT_ID` in `.env`. The frontend uses Google Identity Services and the backend verifies the returned ID token.

### Gemini setup
Put your free Gemini API key in `GEMINI_API_KEY`. The default model is `gemini-3.5-flash-lite`; override `GEMINI_MODEL` if needed. SmartReport supports text plus an optional image. Images are sent only to Gemini for classification and are not stored by HostelFix. The AI call is server-side and never exposed to browser code.

`docker compose up --build` starts the complete stack.

## MS-5 authentication and AI setup

### 1. Create the local environment file

Copy the example file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

You must edit **`.env`**. Never put these values into `frontend/src/app.js` or commit `.env`.

Required values for your MS-5 demo:

```env
SESSION_SECRET=put_a_random_secret_here_at_least_32_characters_long
GOOGLE_CLIENT_ID=YOUR_GOOGLE_WEB_CLIENT_ID.apps.googleusercontent.com
GEMINI_API_KEY=YOUR_FREE_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.5-flash-lite
```

`SESSION_SECRET` is generated by you; it is not supplied by Google or Gemini. The Google client ID is a browser OAuth identifier and is safe to be present in the frontend flow, but the backend still verifies the returned ID token. The Gemini API key is secret and is used only by FastAPI.

### 2. Create the Google OAuth Web Client

Open Google Cloud Console and create/select a project. In the Google Auth Platform / Clients area, create an **OAuth client → Web application**.

For local HostelFix, add this **Authorized JavaScript origin**:

```text
http://localhost:8080
```

Google's current Identity Services documentation requires the JavaScript origin to match the site origin; localhost HTTP is allowed for development. urlGoogle Identity Services setuphttps://developers.google.com/identity/gsi/web/reference/js-reference

Copy the generated Web Client ID and put it into `.env` as `GOOGLE_CLIENT_ID`.

Do **not** put a Google client secret into this project. This implementation uses Google Identity Services in the browser and verifies the ID token on the FastAPI server.

The backend additionally rejects Google accounts unless the ID token is verified and the account belongs to the `iitdh.ac.in` hosted domain. Therefore a Gmail account such as `someone@gmail.com` will not be accepted.

### 3. Create the Gemini API key

Use Google AI Studio to create a Gemini API key and copy it into:

```env
GEMINI_API_KEY=...
```

The Gemini Developer API has a free tier, although model availability and free quotas can change. urlGemini API pricing and free tierhttps://ai.google.dev/gemini-api/docs/pricing

This project uses `gemini-3.5-flash-lite`, which is a stable multimodal model supporting image input and structured output. urlGemini 3.5 Flash-Lite model documentationhttps://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite

### 4. Start the project

From the directory containing `docker-compose.yml`:

```bash
docker compose down
docker compose up --build
```

Wait until the `web` and `api` services are running. Then open:

```text
http://localhost:8080
```

The first build can take several minutes because Docker downloads the Python dependencies and MySQL image.

### 5. Test manual IIT Dharwad registration

On **Create account** use an address ending exactly in:

```text
@iitdh.ac.in
```

The password requirement is **at least 5 characters**.

For example:

```text
Name: Test User
Email: testuser@iitdh.ac.in
Password: Test1
```

Keep the consent checkbox selected.

In the default development configuration:

```env
MAIL_MODE=log
```

no real email is sent. The verification URL is returned by the development API response and logged by the API container. Open that verification URL in the browser, then sign in normally.

### 6. Test Google Sign-In

Use a Google account whose Google Workspace account is an IIT Dharwad `@iitdh.ac.in` account and whose email is verified by Google.

Click **Continue with Google**. If the browser reports `Invalid Google ID token`, first check that the `GOOGLE_CLIENT_ID` in `.env` is the **same Web Client ID** used by the Google button and that `http://localhost:8080` is registered as an authorized JavaScript origin. Then rebuild:

```bash
docker compose down
docker compose up --build
```

### 7. Test SmartReport

Sign in as a student and open **Report an Issue**.

SmartReport accepts either text, an image, or both. Example image tests:

- Upload a photo of a damaged washing machine → SmartReport should suggest **Maintenance → Washing machine**.
- Upload a photo showing a faulty/stuck lift → SmartReport should suggest **Maintenance → Lift malfunction**.
- Upload a dirty washing-machine area → SmartReport should suggest **Housekeeping → Washing machine area cleaning**.

The AI result is only a draft. The student must review the suggested fields before submitting the complaint.

The API sends only the complaint text and optional uploaded image needed for SmartReport. Passwords, email addresses and other account identifiers are not sent to Gemini.

### 8. Run tests

Unit/integration tests:

```bash
python -m pytest -m 'not e2e' -q
```

Frontend syntax check:

```bash
node --check frontend/src/app.js
```

For the Playwright tests, install the browser once:

```bash
python -m playwright install chromium
```

Then, with HostelFix already running:

```bash
python -m pytest tests/e2e -m e2e -q
```

The GitHub Actions workflow installs Chromium automatically and runs the two MS-5 Playwright tests.

### 9. Useful Docker commands

```bash
# Start
Docker compose up --build

# Stop
Docker compose down

# View API logs
Docker compose logs -f api

# View all logs
Docker compose logs -f

# Check running containers
Docker compose ps
```

Use lowercase `docker` rather than `Docker` on Linux/macOS/WSL:

```bash
docker compose ps
docker compose logs -f api
```

If you changed `.env`, rebuild/recreate the API container so the new environment values are loaded:

```bash
docker compose down
docker compose up --build
```


## MS-5 lifecycle and administration

- Similar open complaints are checked before a new report is submitted. Matching uses the exact location and problem type, with housekeeping service date included when applicable. Room-area complaints are excluded from “Me too” matching. The student can choose **Me too** on an existing submitted complaint or continue with a new report.
- “Me too” is enforced by the backend only for `submitted` non-Room complaints and cannot be bypassed through the UI.
- Complaint status transitions are enforced server-side using the design-document state machine. `closed` and `rejected` are final.
- Reporter confirmation changes `resolved -> closed`; a reopen request changes `resolved -> reopened`. Resolved complaints with no response are automatically closed after 7 days with the audit comment `auto-closed: no response`.
- Asset selection is validated against the `asset_locations` relationship, so an asset cannot be attached to an unrelated location.
- Administrators can manage categories, problem types, locations, assets and asset-location links, and set category resolution targets from the Admin Dashboard.
- Admin analytics include status/category/location/problem-type counts, overdue complaints, reopened complaints and average resolution time.
- Staff accounts created by an administrator receive a one-time set-password link. Passwords are hashed with Argon2id before storage.
- Authentication, verification, password-reset and SmartReport operations are rate-limited.
- The SmartReport evaluation set contains 40 manually reviewable cases covering clear reports, incomplete/ambiguous reports, Hinglish, typos, short inputs, partial-location traps and prompt-injection attempts.
