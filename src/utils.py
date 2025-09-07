import os
import json
from pathlib import Path
from typing import Any, Dict

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RAW_DIR = DATA_DIR / "raw"
CACHE_DIR = DATA_DIR / "cache"
POKEAPI_CACHE = CACHE_DIR / "pokeapi"

def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    POKEAPI_CACHE.mkdir(parents=True, exist_ok=True)

def cache_path_for(endpoint: str) -> Path:
    safe = endpoint.strip("/").replace("/", "__")
    return POKEAPI_CACHE / f"{safe}.json"

def load_json_file(p: Path) -> Any:
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json_file(p: Path, data: Any):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
