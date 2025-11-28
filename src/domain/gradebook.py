import pandas as pd
from typing import Optional
from .grade_scale import GradeScale


class Gradebook:
    """
    Encapsulates GPA-related computations using a GradeScale and
    enrollment + course tables.
    """

    def __init__(
        self,
        enrollments: pd.DataFrame,
        courses: pd.DataFrame,
        scale: GradeScale,
        repeat_policy: str = "latest",  # or "highest"
    ):
        self.enrollments = enrollments.copy()
        self.courses = courses.copy()
        self.scale = scale
        self.repeat_policy = repeat_policy

    def _apply_repeat_policy(self, df: pd.DataFrame) -> pd.DataFrame:
        # For repeated courses, either keep latest attempt or highest grade.
        if self.repeat_policy == "latest":
            df_sorted = df.sort_values("term")
            return df_sorted.drop_duplicates(
                subset=["student_id", "course_id"], keep="last"
            )
        elif self.repeat_policy == "highest":
            df_tmp = df.copy()
            df_tmp["grade_tmp"] = df_tmp["grade"].fillna(-1)
            df_sorted = df_tmp.sort_values("grade_tmp")
            out = df_sorted.drop_duplicates(
                subset=["student_id", "course_id"], keep="last"
            )
            return out.drop(columns=["grade_tmp"])
        return df

    def _merged(self) -> pd.DataFrame:
        df = self.enrollments.copy()
        df = df[df["status"] == "completed"]
        df = self._apply_repeat_policy(df)
        merged = df.merge(
            self.courses[["course_id", "credits"]], on="course_id", how="left"
        )
        merged["credits"] = merged["credits"].fillna(0)
        merged["points"] = merged["grade"].apply(self.scale.to_points)
        merged["quality_points"] = merged["points"] * merged["credits"]
        return merged

    def compute_gpa_table(self) -> pd.DataFrame:
        """
        Returns DataFrame with columns:
        student_id, total_credits, quality_points, gpa
        """
        merged = self._merged()
        grouped = merged.groupby("student_id").agg(
            total_credits=("credits", "sum"),
            quality_points=("quality_points", "sum"),
        )
        grouped["gpa"] = (grouped["quality_points"] / grouped["total_credits"]).round(
            2
        )
        return grouped.reset_index()

    def student_gpa(self, student_id: str) -> Optional[float]:
        tbl = self.compute_gpa_table()
        row = tbl[tbl["student_id"] == student_id]
        if row.empty:
            return None
        return float(row["gpa"].iloc[0])

    def term_gpa(self, student_id: str, term: str) -> Optional[float]:
        df = self.enrollments.copy()
        df = df[
            (df["student_id"] == student_id)
            & (df["term"] == term)
            & (df["status"] == "completed")
        ]
        if df.empty:
            return None
        df = df.merge(
            self.courses[["course_id", "credits"]], on="course_id", how="left"
        )
        df["credits"] = df["credits"].fillna(0)
        df["points"] = df["grade"].apply(self.scale.to_points)
        df["quality_points"] = df["points"] * df["credits"]
        total_credits = df["credits"].sum()
        if total_credits == 0:
            return None
        gpa = df["quality_points"].sum() / total_credits
        return round(float(gpa), 2)