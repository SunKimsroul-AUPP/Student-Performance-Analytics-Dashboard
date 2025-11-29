# Project Structure

This file summarizes the top-level structure of the repository and key files for quick navigation.

## Overview

- Repository: Student-Performance-Analytics-Dashboard
- Purpose: Student performance analytics and dashboarding utilities

## Top-level tree
*** End Patch
        advisors.js
        app.js
        auth.js
        courses.js
        data.js
        faculty.js
        login.js
        students.js
tools/
    generate_full_prereqs.py
```

## Notes

- The `src/` directory contains the application code separated by concerns (api, auth, data_access, domain, graph, models, services, utils).
- Static UI files are under `static/` (HTML, CSS, JS) — good starting point if you want to modify the frontend.
- Data CSVs are in `data/` and used by loader scripts in `src/data_access` and `scripts/`.
- Configuration lives in `config/settings.yaml` and environment-specific settings can be added there.

## Quick commands

Open the project root in VS Code:
# Project Structure

Below is an updated tree-style layout that matches the repository's current files and folders, shown in the ASCII style you requested.

```
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

## Notes

- This mirrors your requested ASCII/tree style while reflecting the repository's actual structure and filenames.
- I used `src/` (the current code directory) rather than renaming it to `app/`. If you prefer `app/` instead of `src/`, I can update the file (and optionally rename the folder in the repo).

## Next steps

- Commit the change:

```powershell
git add "PROJECT_STRUCTURE.md"
git commit -m "Update project structure to match repository layout"
```

- Want this structure exported as JSON, included in the `README.md`, or committed automatically? Tell me which and I'll do it.
