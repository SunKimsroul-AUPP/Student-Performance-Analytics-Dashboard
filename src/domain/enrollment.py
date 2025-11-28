from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Enrollment:
    """
    Represents a student's enrollment in a course for a specific term.
    """
    student_id: str
    course_id: str
    term: str
    grade: Optional[float] = None
    attendance_pct: Optional[float] = None
    status: str = "completed"  # completed, in_progress, withdrawn