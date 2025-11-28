from pathlib import Path
from typing import Dict
import pandas as pd


def load_csvs(base_dir: Path) -> Dict[str, pd.DataFrame]:
    students = pd.read_csv(base_dir / "students.csv")
    courses = pd.read_csv(base_dir / "courses.csv")
    enrollments = pd.read_csv(base_dir / "enrollments.csv")
    prereq_path = base_dir / "prerequisites.csv"
    if prereq_path.exists():
        prereqs = pd.read_csv(prereq_path)
    else:
        prereqs = pd.DataFrame(columns=["course_id", "prereq_id"])
    return {
        "students": students,
        "courses": courses,
        "enrollments": enrollments,
        "prerequisites": prereqs,
    }