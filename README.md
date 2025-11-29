# Student Performance Analytics Dashboard

A FastAPI + Pandas demo application that provides role-based dashboards for analyzing student performance, course outcomes, and curriculum structure using **synthetic** data (no real student data).

The app shows how a school might monitor:

- Student GPA, attendance, DFW history, and credits.
- Course pass/DFW rates by department and term.
- At-risk students for advisors.
- Prerequisite relationships and course dependency listings for faculty.
- CSV-based data management for admins.

> **Important**: This project is for learning/demo purposes only. Do **not** upload or use real student data.

---

## 1. Features

### 1.1 Role-based dashboards

The app uses JWT auth with four roles:

- **Admin**
  - Access to **all** dashboards: Overview, Faculty, Advisor, Student, Courses, Data Admin.
  - Can upload/download CSV data.
- **Faculty**
  - Access to **Overview** and **Faculty** dashboard.
  - In this implementation, faculty may also access **Advisor** and **Courses** views.
- **Advisor**
  - Access to **Overview** and **Advisor** dashboard.
  - In this implementation, advisors may also access **Faculty** and **Courses** views.
- **Student**
  - Access to **Student** dashboard and read-only **Overview**.
  - Students log in using their **student ID** (e.g., `S001`).

Each dashboard is a plain HTML page served by FastAPI’s static files, with a small JS file that calls the API.

### 1.2 Student-level metrics

Across the Overview GPA leaderboard, Advisor At‑Risk table, and Student dashboard, each student has:

- **GPA** – computed from course grades via `Gradebook`.
- **Avg Attendance (%)** – mean `attendance_pct` across completed enrollments.
- **DFW Count** – number of completed courses with grade below the passing threshold.
- **Credits Attempted** – sum of course `credits` for completed enrollments.
- **Major** and **Cohort year**.

These metrics come from:

```python
AnalyticsService.student_summary_table()
```

Exposed via:

- `GET /api/metrics/student-summary`

---

## 2. Dashboards

### 2.1 Overview (`/`)

High-level view for leadership:

- **Headline metrics**:
  - Total number of students.
  - Average GPA.
  - Number of at‑risk students.
- **GPA Leaderboard** (table):
  - Student name / ID.
  - Major, Cohort.
  - GPA, Total credits.
  - Avg Attendance (%), DFW Count, Credits Attempted.
- **At-Risk Students** (compact list):
  - Name, GPA, risk score, and flags.
- **Cohort GPA Trend**:
  - Chart.js line chart showing **mean** and **median** GPA by cohort year.
  - Data from `GET /api/metrics/cohort-gpa`.

Implemented in `static/js/app.js` calling:

- `GET /api/metrics/student-summary`
- `GET /api/risk/at-risk`
- `GET /api/metrics/cohort-gpa`

### 2.2 Faculty View (`/faculty.html`)

For department chairs and instructors:

- Filters by **department** and **term**.
- **Course Pass Rates** chart.
- **Course DFW Rates** chart.
 - **All Courses & Prerequisites**: a per-course listing of direct prerequisites (or "None" if none).
- **Download Course Metrics (CSV)**:
  - Button that calls `GET /api/metrics/pass-rates/export` with filters.

Implemented in `static/js/faculty.js` using:

- `GET /api/metrics/pass-rates`
- `GET /api/metrics/dfw-rates`
- `GET /api/graph/prerequisites` (summary) and `GET /api/graph/prerequisites/full` (full per-course listing)

### 2.3 Advisor View (`/advisors.html`)

For academic advisors:

- Filters by **major** and **cohort** year.
- **At-Risk Students** table with:
  - Student, Major, Cohort.
  - GPA.
  - Avg Attendance (%).
  - DFW Count.
  - Credits Attempted.
  - Risk Score + label (High / Medium / Low / Unknown).
  - Risk flags (e.g., `LOW_GPA`, `LOW_ATTENDANCE`, `DFW_HISTORY`).

Built in `static/js/advisors.js` from:

- `GET /api/metrics/student-summary` (metrics).
- `GET /api/risk/at-risk` (scores & flags).

### 2.4 Student View (`/students.html`)

For individual students (and admin inspecting any student):

- When logged in as **student** (e.g., username `S003`):
  - Automatically shows **only that student’s** data:
    - Major, Cohort, GPA.
    - Avg Attendance (%), DFW Count, Credits Attempted.
    - Enrollment table (term, course, title, grade, attendance).
- When logged in as **admin**:
  - Shows an admin-only search box to inspect any student ID.
  - Uses the same metrics and enrollment table.

Note: For the demo, the `/api/students/{student_id}/enrollments` endpoint is implemented as a public endpoint to make it easier for an admin to inspect student records. In a production deployment you should restore proper authentication/authorization checks so that students can only view their own data and admins/faculty/advisors require appropriate roles. Front-end logic is in `static/js/students.js`.

### 2.5 Courses View (`/courses.html`)

Cross-course analytics:

- **Course Pass Rates** bar chart.
- **Course DFW Rates** bar chart.
- Tabular summary by course:
  - Course ID, Title, Department, Level, Pass Rate %, DFW Rate %.

Powered by:

- `GET /api/metrics/pass-rates`
- `GET /api/metrics/dfw-rates`

The Navbar on this page shows the current user + Logout using shared navbar helpers from `login.js`.

### 2.6 Data Admin (`/data.html`)

CSV data management UI. NOTE: for the local demo some admin endpoints are intentionally left public to simplify data inspection and uploading; you must secure these endpoints in a real deployment.

- **Current data status**:
  - Calls `GET /api/admin/data-status` and shows a JSON summary of tables and columns.
- **Download current CSVs**:
  - Download buttons call:
    - `/api/admin/download/students`
    - `/api/admin/download/courses`
    - `/api/admin/download/enrollments`
    - `/api/admin/download/prerequisites`
- **Upload new CSVs**:
  - Four upload forms (students, courses, enrollments, prerequisites).
  - POST to `/api/admin/upload/{table_name}` with multipart form data.

Implementation:

- `static/js/data.js`
- Routes in `router.py` under `/api/admin/*` (in this demo they are accessible without admin role; protect them for production).

---

## 3. Authentication & Roles

Auth is defined in `auth/auth.py` using:

- **Simple SHA-256** hashing for demo passwords (not for production).
- **JWT** via `python-jose`.
- `OAuth2PasswordBearer` for FastAPI dependencies.

### 3.1 Fixed demo accounts

Configured in `_fake_users_db`:

- `admin`   / `admin123`   → role: `admin`
- `faculty` / `faculty123` → role: `faculty`
- `advisor` / `advisor123` → role: `advisor`

### 3.2 Dynamic student accounts

Any username that:

- Matches a `student_id` in the `students` table, and
- Uses password `student123`

is treated as a **student** user:

- `role = "student"`
- `student_id = username`

Logic in `_maybe_make_student_user(username)`:

- Uses `DataService.instance().get_table("students")` to find the student.
- Synthesizes a user with the shared student password.

### 3.3 `/api/auth/token` and JWT

The login endpoint:

```python
@router.post("/auth/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}
```

Front-end `static/js/login.js`:

- Sends `POST /api/auth/token` with `username` and `password`.
- On success, stores:
  - `access_token` (key: `"access_token"`) – used for `Authorization: Bearer` headers.
  - `spa_token`, `spa_role`, `spa_username` – for compatibility with older `auth.js`-based pages.
- Redirects to `/`.

### 3.4 Frontend helpers

There are two layers of auth helpers:

1. **New-style helpers (navbar + Bearer header):**  
   In `static/js/login.js`:
   - `getAccessToken()`
   - `setAccessToken(token)`
   - `getAuthHeaders(extra)` – returns `{ Authorization: "Bearer …", ...extra }`.
   - `initNavbarAuthShared()` – populates `#nav-user` and wires `#logout-btn`:
     - Called from `index.html`, `courses.html`, and `data.html`.

2. **Legacy helpers for role-based pages:**  
   In `static/js/auth.js`:
   - `getAccessToken()` and `getAuthHeaders(extra)` (same token key).
   - `requireLogin()` – redirects to `/login.html` if no token.
   - `fetchCurrentUser()` – calls `/api/auth/me`.
   - `getCurrentRole()`, `getCurrentUsername()` – derived from stored `spa_role` / `spa_username` or session cache.
   - `setupLoginLink()` – updates `#role-indicator` and `#login-link` on top-right of faculty/advisors/students pages.

> Together, this lets older pages use `requireLogin()` / `setupLoginLink()`, while newer dashboards and the navbar share the same `access_token` and logout behavior.

---

## 4. Data Model & Services

Data is loaded from CSV files via `DataService`. Typical layout:

- `data/students.csv`
- `data/courses.csv`
- `data/enrollments.csv`
- `data/prerequisites.csv`

### 4.1 DataService

Singleton in `services/data_service.py`:

- Loads CSVs at startup (or on first access).
- Provides:
  - `get_datasets()` → dict of all tables.
  - `get_table(name)` → individual DataFrame.
  - `replace_table_from_file(name, path)` → used by Data Admin upload endpoint.
  - `status()` → used by `/api/admin/data-status`.

### 4.2 Gradebook & Analytics

- `Gradebook`:
  - Computes GPA using a grade scale (`domain/grade_scale.py`).
  - Works with `enrollments` and `courses`.
- `AnalyticsService`:
  - `gpa_table(major?, cohort_year?)`
  - `pass_rates(department?, term?)`
  - `dfw_rates(department?, term?)`
  - `attendance_grade_correlation()`
  - `cohort_gpa_summary()`
  - `student_summary_table()` – consolidated per‑student metrics.

### 4.3 RiskService & GraphService

- `RiskService`:
  - Ingests GPA table and enrollments.
  - Produces `at_risk_students()` with scores and flags.
  - Exposed as `GET /api/risk/at-risk`.

- `GraphService`:
  - Builds a graph from `prerequisites` table.
  - Detects cycles and summarizes gateway structure.
  - Exposed as `GET /api/graph/prerequisites`.

---

## 5. API Overview

All endpoints are under `/api`.

### 5.1 Auth & health

- `GET  /api/health` – simple health check.
- `POST /api/auth/token` – JWT login.
- `GET  /api/auth/me` – current user info (must be implemented using `get_current_user`).

### 5.2 Metrics (public)

- `GET /api/metrics/gpa` – list of GPA entries (`GPAEntry`).
- `GET /api/metrics/pass-rates` – course pass rates (`PassRateEntry`).
- `GET /api/metrics/dfw-rates` – course DFW rates (`DFWRateEntry`).
- `GET /api/metrics/attendance-correlation` – correlation summary.
- `GET /api/metrics/cohort-gpa` – cohort GPA summary (`CohortGPAEntry`).
- `GET /api/metrics/student-summary` – per-student enriched metrics table.

### 5.3 Risk & graph

- `GET /api/risk/at-risk` – list of `RiskEntry`.
- `GET /api/graph/prerequisites` – `GraphSummary` (summary of cycles/depths/gateway candidates).
- `GET /api/graph/prerequisites/full` – full per-course listing: each item contains `course_id`, optional `title`, and `prerequisites: [{course_id, title?}, ...]`.

### 5.4 Students

- `GET /api/students` – list basic student info: id, name, major, cohort.
- `GET /api/students/{student_id}/enrollments` – enrollments for one student.
  - Note: in this demo the enrollments endpoint is left public to simplify admin inspection. Reinstate authentication/authorization checks for production so students can only view their own records.

### 5.5 Data Admin (admin only)

- `GET  /api/admin/data-status` – summary of tables and column names.
- `GET  /api/admin/download/{table_name}` – stream CSV for one table.
- `POST /api/admin/upload/{table_name}` – upload (replace) a table from CSV.

Allowed `table_name` values: `students`, `courses`, `enrollments`, `prerequisites`.

### 5.6 CSV Exports

- `GET /api/metrics/gpa/export`
- `GET /api/metrics/pass-rates/export`

These return CSV files for external analysis.

---

## 6. Running the App

### 6.1 Requirements

- **Python** 3.9+ (3.10+ recommended).
- **pip** (or poetry/pipenv if you prefer).
- Packages (in `requirements.txt`), e.g.:

```text
fastapi
uvicorn[standard]
pandas
numpy
networkx
scipy
pydantic
pyyaml
python-multipart
python-jose[cryptography]
```

### 6.2 Install

From project root:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 6.3 Configuration

`utils/config_loader.py` loads settings (e.g. from `config/settings.yaml`). Make sure it defines:

```yaml
app:
  title: "Student Performance Analytics Dashboard"

auth:
  secret_key: "CHANGE_ME_TO_A_RANDOM_SECRET"
  algorithm: "HS256"
  access_token_expire_minutes: 60

data:
  data_dir: "data"   # where students.csv, courses.csv, etc. live
```

Adjust keys/paths based on your actual `config_loader` code.

### 6.4 Start FastAPI

From the project root (where `app/main.py` lives):

```bash
uvicorn app.main:app --reload
```

Then visit:

- App:
  - `http://127.0.0.1:8000/login.html` – Login.
  - `http://127.0.0.1:8000/` – Overview dashboard.
  - `http://127.0.0.1:8000/faculty.html`
  - `http://127.0.0.1:8000/advisors.html`
  - `http://127.0.0.1:8000/students.html`
  - `http://127.0.0.1:8000/courses.html`
  - `http://127.0.0.1:8000/data.html`
- API docs:
  - `http://127.0.0.1:8000/docs`
  - `http://127.0.0.1:8000/redoc`

### 6.5 Demo logins

On `/login.html`, use:

- `admin` / `admin123`
- `faculty` / `faculty123`
- `advisor` / `advisor123`
- Any `student_id` from `students.csv` / `student123` (e.g., `S001 / student123`).

The Navbar and page-level JS then enforce which dashboards you can see.

---

## 7. Project Structure (simplified)

```text
project/
├─ README.md
├─ requirements.txt
├─ config/
│  └─ settings.yaml
├─ data/
│  ├─ students.csv
│  ├─ courses.csv
│  ├─ enrollments.csv
│  ├─ prerequisites.csv
│  └─ inferred_prerequisites.csv
├─ notebooks/
│  └─ exploration.ipynb
├─ scripts/
│  └─ generate_full_prereqs.py
├─ src/
│  ├─ __init__.py
│  ├─ api/
│  │  ├─ __init__.py
│  │  ├─ main.py          # FastAPI app (entry), static mount
│  │  └─ router.py        # API route registrations
│  ├─ auth/
│  │  ├─ ___init___.py
│  │  └─ auth.py          # JWT auth, user store, roles, require_role()
│  ├─ data_access/
│  │  ├─ __init__.py
│  │  ├─ loaders.py
│  │  └─ validators.py
│  ├─ domain/
│  │  ├─ __init__.py
│  │  ├─ course.py
│  │  ├─ enrollment.py
│  │  ├─ grade_scale.py
│  │  ├─ gradebook.py
│  │  └─ student.py
│  ├─ graph/
│  │  ├─ __init__.py
│  │  └─ prereq_graph.py
│  ├─ models/
│  │  ├─ __init__.py
│  │  └─ dto.py           # Pydantic models / DTOs
│  ├─ services/
│  │  ├─ __init__.py
│  │  ├─ analytics_service.py
│  │  ├─ data_service.py
│  │  ├─ graph_service.py
│  │  ├─ loader_service.py
│  │  └─ risk_service.py
│  └─ utils/
│     ├─ __init__.py
│     ├─ config_loader.py
│     ├─ exceptions.py
│     └─ logging.py
├─ static/
│  ├─ index.html          # Overview
│  ├─ faculty.html        # Faculty view
│  ├─ advisors.html       # Advisor view
│  ├─ students.html       # Student view
│  ├─ courses.html        # Courses view
│  ├─ data.html           # Data Admin
│  ├─ login.html          # Login page
│  ├─ css/
│  │  └─ styles.css
│  └─ js/
│     ├─ advisors.js
│     ├─ app.js           # Overview logic
│     ├─ auth.js
│     ├─ courses.js
│     ├─ data.js
│     ├─ faculty.js
│     ├─ login.js
│     └─ students.js
└─ tools/
    └─ generate_full_prereqs.py
```

---

## 8. Possible Extensions

If you want to build on this:

- Replace CSV with a real DB (SQLite/Postgres + SQLAlchemy).
- Add more sophisticated risk scoring and visualizations.
- Implement weekly/monthly trend charts for GPA and attendance.
- Add API keys for automated exports.
- Add test coverage for analytics and risk logic with `pytest`.

This project is already a solid foundation for showing skills in:

- Python data analytics (pandas).
- Web API design (FastAPI).
- Role-based access control and JWT.
- A small, clean Bootstrap + JS front-end.
