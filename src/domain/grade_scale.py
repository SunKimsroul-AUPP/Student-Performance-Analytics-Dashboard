from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class GradeBand:
    min: float
    max: float
    points: float


class GradeScale:
    """
    Maps numeric grades (0–100) to GPA points (0–4).
    """

    def __init__(self, bands: List[GradeBand], name: str = "standard"):
        self.bands = bands
        self.name = name

    def to_points(self, grade: float | None) -> float:
        if grade is None:
            return 0.0
        for band in self.bands:
            if band.min <= grade <= band.max:
                return band.points
        return 0.0


default_scale = GradeScale(
    bands=[
        GradeBand(90, 100, 4.0),
        GradeBand(80, 89.999, 3.0),
        GradeBand(70, 79.999, 2.0),
        GradeBand(60, 69.999, 1.0),
        GradeBand(0, 59.999, 0.0),
    ],
    name="standard",
)