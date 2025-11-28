from pathlib import Path
from typing import Dict
import pandas as pd
from ..data_access.loaders import load_csvs
from ..data_access.validators import (
    validate_students,
    validate_courses,
    validate_enrollments,
)
from ..utils.config_loader import load_settings


class LoaderService:
    """
    Loads and validates CSV data according to config.
    """

    def __init__(self):
        settings = load_settings()
        base_dir = Path(settings["app"]["data_dir"])
        if not base_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {base_dir}")
        self.datasets: Dict[str, pd.DataFrame] = load_csvs(base_dir)
        validate_students(self.datasets["students"])
        validate_courses(self.datasets["courses"])
        validate_enrollments(self.datasets["enrollments"])

    def get_datasets(self) -> Dict[str, pd.DataFrame]:
        return self.datasets