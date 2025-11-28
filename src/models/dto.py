from typing import List, Optional, Dict
from pydantic import BaseModel


class GPAEntry(BaseModel):
    student_id: str
    name: Optional[str] = None
    major: Optional[str] = None
    cohort_year: Optional[int] = None
    total_credits: float
    quality_points: float
    gpa: float


class PassRateEntry(BaseModel):
    course_id: str
    title: str
    department: Optional[str] = None
    level: Optional[int] = None
    pass_rate: float


class DFWRateEntry(BaseModel):
    course_id: str
    title: str
    department: Optional[str] = None
    level: Optional[int] = None
    dfw_rate: float


class AttendanceCorrelation(BaseModel):
    pearson: Optional[float]
    spearman: Optional[float]


class CohortGPAEntry(BaseModel):
    cohort_year: int
    mean: float
    median: float
    count: int


class RiskEntry(BaseModel):
    student_id: str
    name: Optional[str] = None
    gpa: float
    flags: List[str]
    score: float                    # composite risk score
    avg_attendance: Optional[float] = None
    dfw_count: Optional[int] = None


class GraphSummary(BaseModel):
    cycle_detected: bool
    # Map of course_id -> depth in prerequisite graph
    depths: Optional[Dict[str, int]] = None

    class GatewayCandidate(BaseModel):
        course_id: str
        dependents: int
        title: Optional[str] = None

    # Top gateway candidates (course_id + number of dependents)
    gateway_candidates: Optional[List[GatewayCandidate]] = None