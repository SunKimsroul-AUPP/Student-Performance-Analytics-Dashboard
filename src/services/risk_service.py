import pandas as pd
from typing import List, Dict, Any

from ..utils.config_loader import load_settings


class RiskService:
    """
    Computes risk flags and a composite risk score for students based on:
    - GPA
    - Attendance
    - DFW history (grades < dfw_grade_threshold)

    Risk rules (from config):
    - LOW_GPA:         GPA < gpa_threshold
    - LOW_ATTENDANCE:  avg_attendance < attendance_threshold
    - DFW_HISTORY:     dfw_count >= 1

    Composite risk score:
        gpa_deficit        = max(0, gpa_threshold - gpa)
        attendance_deficit = max(0, attendance_threshold - avg_attendance) / 100
        dfw_load           = dfw_count

        risk_score =
            gpa_weight        * gpa_deficit
          + attendance_weight * attendance_deficit
          + dfw_weight        * dfw_load
    """

    def __init__(self, gpa_table: pd.DataFrame, enrollments: pd.DataFrame):
        self.gpa_table = gpa_table.copy()
        self.enrollments = enrollments.copy()

        cfg = load_settings().get("risk", {})
        self.gpa_threshold: float = float(cfg.get("gpa_threshold", 2.0))
        self.attendance_threshold: float = float(cfg.get("attendance_threshold", 70.0))
        self.dfw_cutoff: float = float(cfg.get("dfw_grade_threshold", 60.0))

        self.gpa_weight: float = float(cfg.get("gpa_weight", 1.0))
        self.attendance_weight: float = float(cfg.get("attendance_weight", 1.0))
        self.dfw_weight: float = float(cfg.get("dfw_weight", 0.5))

        # Precompute per-student attendance & dfw_count (joined with GPA)
        self._student_metrics = self._compute_student_risk_metrics()

    def _compute_student_risk_metrics(self) -> pd.DataFrame:
        """
        Build a per-student table with:
        - gpa
        - avg_attendance
        - dfw_count
        - any extra columns already in gpa_table (e.g., name, major, cohort_year)
        """
        enr = self.enrollments.copy()
        enr = enr[enr["status"] == "completed"]

        # Attendance per student
        attendance = (
            enr.groupby("student_id")["attendance_pct"]
            .mean()
            .rename("avg_attendance")
        )

        # DFW count per student (grade < dfw_cutoff)
        dfw_mask = enr["grade"] < self.dfw_cutoff
        dfw_count = (
            enr[dfw_mask]
            .groupby("student_id")["course_id"]
            .count()
            .rename("dfw_count")
        )

        metrics = (
            self.gpa_table.set_index("student_id")
            .join(attendance, how="left")
            .join(dfw_count, how="left")
            .reset_index()
        )
        # Reasonable defaults if metrics missing
        metrics["avg_attendance"] = metrics["avg_attendance"].fillna(100.0)
        metrics["dfw_count"] = metrics["dfw_count"].fillna(0).astype(int)
        return metrics

    def risk_flags_for(self, student_id: str) -> List[str]:
        """
        Return textual flags like ["LOW_GPA", "LOW_ATTENDANCE", "DFW_HISTORY"].
        """
        row = self._student_metrics[
            self._student_metrics["student_id"] == student_id
        ]
        if row.empty:
            return []

        row = row.iloc[0]
        flags: List[str] = []

        gpa = float(row["gpa"])
        if gpa < self.gpa_threshold:
            flags.append("LOW_GPA")

        avg_att = float(row["avg_attendance"])
        if avg_att < self.attendance_threshold:
            flags.append("LOW_ATTENDANCE")

        dfw_count = int(row["dfw_count"])
        if dfw_count > 0:
            flags.append("DFW_HISTORY")

        return flags

    def risk_score_for(self, student_id: str) -> float:
        """
        Compute the composite risk score for a student.
        """
        row = self._student_metrics[
            self._student_metrics["student_id"] == student_id
        ]
        if row.empty:
            return 0.0

        row = row.iloc[0]
        gpa = float(row["gpa"])
        avg_att = float(row["avg_attendance"])
        dfw_count = int(row["dfw_count"])

        gpa_deficit = max(0.0, self.gpa_threshold - gpa)
        attendance_deficit = max(0.0, self.attendance_threshold - avg_att) / 100.0
        dfw_load = dfw_count

        score = (
            self.gpa_weight * gpa_deficit
            + self.attendance_weight * attendance_deficit
            + self.dfw_weight * dfw_load
        )
        return float(score)

    def at_risk_students(self) -> List[Dict[str, Any]]:
        """
        Return a list of students who have any risk flags, including:
        - student_id, name, gpa
        - flags
        - score (composite risk score)
        - avg_attendance, dfw_count (for convenience)
        Sorted by descending risk score.
        """
        results: List[Dict[str, Any]] = []

        for _, row in self._student_metrics.iterrows():
            sid = row["student_id"]
            flags = self.risk_flags_for(sid)
            if not flags:
                continue

            entry = {
                "student_id": sid,
                "name": row.get("name", ""),
                "gpa": float(row["gpa"]),
                "flags": flags,
                "score": self.risk_score_for(sid),
                "avg_attendance": float(row["avg_attendance"]),
                "dfw_count": int(row["dfw_count"]),
            }
            results.append(entry)

        results.sort(key=lambda r: r["score"], reverse=True)
        return results