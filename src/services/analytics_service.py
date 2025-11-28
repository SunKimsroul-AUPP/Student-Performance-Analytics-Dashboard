import pandas as pd
from typing import Dict, Optional
from scipy import stats
from ..domain.gradebook import Gradebook


class AnalyticsService:
    """
    Provides high-level analytics built on top of Gradebook and raw tables.
    """

    def __init__(
        self,
        gradebook: Gradebook,
        students: pd.DataFrame,
        courses: pd.DataFrame,
        enrollments: pd.DataFrame,
    ):
        self.gradebook = gradebook
        self.students = students
        self.courses = courses
        self.enrollments = enrollments

    def gpa_table(
        self,
        major: Optional[str] = None,
        cohort_year: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Optionally filter GPA table by major and/or cohort_year.
        """
        tbl = self.gradebook.compute_gpa_table()
        merged = tbl.merge(self.students, on="student_id", how="left")
        if major:
            merged = merged[merged["major"] == major]
        if cohort_year is not None:
            merged = merged[merged["cohort_year"] == cohort_year]
        return merged

    def pass_rates(
        self,
        department: Optional[str] = None,
        term: Optional[str] = None,
    ) -> pd.DataFrame:
        df = self.enrollments.copy()
        df = df[df["status"] == "completed"]
        if term:
            df = df[df["term"] == term]
        df["passed"] = df["grade"] >= 60
        rates = df.groupby("course_id")["passed"].mean().reset_index()
        rates.rename(columns={"passed": "pass_rate"}, inplace=True)
        merged = rates.merge(self.courses, on="course_id", how="left")
        if department:
            merged = merged[merged["department"] == department]
        return merged

    def dfw_rates(
        self,
        department: Optional[str] = None,
        term: Optional[str] = None,
    ) -> pd.DataFrame:
        df = self.enrollments.copy()
        df = df[df["status"] == "completed"]
        if term:
            df = df[df["term"] == term]
        df["dfw"] = df["grade"] < 60
        rates = df.groupby("course_id")["dfw"].mean().reset_index()
        rates.rename(columns={"dfw": "dfw_rate"}, inplace=True)
        merged = rates.merge(self.courses, on="course_id", how="left")
        if department:
            merged = merged[merged["department"] == department]
        return merged

    def attendance_grade_correlation(self) -> Dict[str, float | None]:
        df = self.enrollments.dropna(subset=["attendance_pct", "grade"])
        if len(df) < 3:
            return {"pearson": None, "spearman": None}
        pearson, _ = stats.pearsonr(df["attendance_pct"], df["grade"])
        spearman_result = stats.spearmanr(df["attendance_pct"], df["grade"])
        return {
            "pearson": round(float(pearson), 3),
            "spearman": round(float(spearman_result.correlation), 3),
        }

    def cohort_gpa_summary(self) -> pd.DataFrame:
        gpa_tbl = self.gradebook.compute_gpa_table()
        merged = gpa_tbl.merge(self.students, on="student_id", how="left")
        return (
            merged.groupby("cohort_year")["gpa"]
            .agg(["mean", "median", "count"])
            .reset_index()
        )

    def student_summary_table(self) -> pd.DataFrame:
        """
        Return one row per student with:
        - GPA (from gradebook)
        - Avg attendance across completed enrollments
        - DFW_count (# of completed enrollments with grade < 60)
        - Credits attempted (sum of course credits across completed enrollments)
        - Basic student info (name, major, cohort_year)
        """
        gpa_tbl = self.gradebook.compute_gpa_table()  # student_id, total_credits, quality_points, gpa

        # Work on completed enrollments
        enr = self.enrollments.copy()
        enr = enr[enr["status"] == "completed"]

        # Merge with courses to get credits
        courses = self.courses[["course_id", "credits"]].copy()
        enr = enr.merge(courses, on="course_id", how="left")

        # Average attendance per student
        attendance = (
            enr.groupby("student_id")["attendance_pct"]
            .mean()
            .rename("avg_attendance")
        )

        # DFW count per student (grade < 60)
        dfw_mask = enr["grade"] < 60
        dfw_count = (
            enr[dfw_mask]
            .groupby("student_id")["course_id"]
            .count()
            .rename("dfw_count")
        )

        # Credits attempted per student
        credits_attempted = (
            enr.groupby("student_id")["credits"]
            .sum()
            .rename("credits_attempted")
        )

        # Combine with GPA table
        summary = (
            gpa_tbl.set_index("student_id")
            .join(attendance, how="left")
            .join(dfw_count, how="left")
            .join(credits_attempted, how="left")
            .reset_index()
        )

        # Merge with student metadata (name, major, cohort_year, etc.)
        summary = summary.merge(self.students, on="student_id", how="left")

        # Fill NaNs with defaults
        summary["avg_attendance"] = summary["avg_attendance"].fillna(0.0)
        summary["dfw_count"] = summary["dfw_count"].fillna(0).astype(int)
        summary["credits_attempted"] = summary["credits_attempted"].fillna(0.0)

        return summary