import pandas as pd


def validate_students(df: pd.DataFrame) -> None:
    required = {"student_id", "name"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"students.csv missing columns: {missing}")
    if df["student_id"].duplicated().any():
        raise ValueError("Duplicate student_id values in students.csv")


def validate_courses(df: pd.DataFrame) -> None:
    required = {"course_id", "title", "credits"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"courses.csv missing columns: {missing}")
    if (df["credits"] < 0).any():
        raise ValueError("Negative credits in courses.csv")


def validate_enrollments(df: pd.DataFrame) -> None:
    required = {
        "student_id",
        "course_id",
        "term",
        "grade",
        "attendance_pct",
        "status",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"enrollments.csv missing columns: {missing}")
    df["grade"] = pd.to_numeric(df["grade"], errors="coerce").clip(0, 100)
    df["attendance_pct"] = (
        pd.to_numeric(df["attendance_pct"], errors="coerce").clip(0, 100)
    )
    df["status"] = df["status"].fillna("completed")