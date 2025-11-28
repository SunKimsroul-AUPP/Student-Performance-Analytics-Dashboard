from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Course:
    """
    Represents a course in the catalog.
    """
    course_id: str
    title: str
    credits: int
    department: Optional[str] = None
    level: Optional[int] = None