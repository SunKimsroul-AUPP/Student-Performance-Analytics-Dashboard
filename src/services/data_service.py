from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

import pandas as pd

from ..data_access.loaders import load_csvs
from ..data_access.validators import (
    validate_students,
    validate_courses,
    validate_enrollments,
)
from ..utils.config_loader import load_settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DataService:
    """
    Singleton-like service that holds in-memory DataFrames for
    students, courses, enrollments, and prerequisites.
    Supports reloads from disk and from uploaded CSV files.
    """

    _instance: Optional["DataService"] = None

    def __init__(self) -> None:
        settings = load_settings()
        self.base_dir = Path(settings["app"]["data_dir"])
        self.datasets: Dict[str, pd.DataFrame] = {}
        self.last_loaded: Optional[datetime] = None
        self.reload_from_disk()

    @classmethod
    def instance(cls) -> "DataService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def reload_from_disk(self) -> None:
        """Load all CSVs from the configured data directory."""
        logger.info("Reloading data from disk: %s", self.base_dir)
        self.datasets = load_csvs(self.base_dir)
        self._validate_all()
        self.last_loaded = datetime.utcnow()

    def _validate_all(self) -> None:
        validate_students(self.datasets["students"])
        validate_courses(self.datasets["courses"])
        validate_enrollments(self.datasets["enrollments"])

    def get_datasets(self) -> Dict[str, pd.DataFrame]:
        return self.datasets

    def get_table(self, name: str) -> pd.DataFrame:
        if name not in self.datasets:
            raise ValueError(f"Unknown table: {name}")
        return self.datasets[name]

    def replace_table_from_file(self, name: str, file_path: Path) -> None:
        """
        Replace one table (students/courses/enrollments/prerequisites)
        from an uploaded CSV file, validate, and update cache.
        """
        logger.info("Replacing table '%s' from file %s", name, file_path)
        df = pd.read_csv(file_path)

        # Validate by table
        if name == "students":
            validate_students(df)
        elif name == "courses":
            validate_courses(df)
        elif name == "enrollments":
            validate_enrollments(df)
        elif name == "prerequisites":
            required = {"course_id", "prereq_id"}
            missing = required - set(df.columns)
            if missing:
                raise ValueError(
                    f"prerequisites.csv missing required columns: {missing}"
                )
        else:
            raise ValueError(f"Unknown table: {name}")

        self.datasets[name] = df
        self.last_loaded = datetime.utcnow()
        logger.info("Table '%s' replaced successfully.", name)

    def status(self) -> Dict[str, object]:
        """Return basic status about current datasets."""
        return {
            "last_loaded": self.last_loaded.isoformat() if self.last_loaded else None,
            "tables": {name: len(df) for name, df in self.datasets.items()},
        }