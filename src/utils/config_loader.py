from pathlib import Path
from typing import Dict, Any
import yaml

_CONFIG_CACHE: Dict[str, Any] | None = None


def load_settings() -> Dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    config_path = Path("config/settings.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        _CONFIG_CACHE = yaml.safe_load(f)
    return _CONFIG_CACHE