from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Student:
    """
    Represents a single student.
    """
    student_id: str
    name: str
    major: Optional[str] = None
    cohort_year: Optional[int] = None