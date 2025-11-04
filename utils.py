import hashlib, os, json, time, re
from typing import Any, Dict

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def _key(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def cache_get(key: str):
    fp = os.path.join(CACHE_DIR, key + ".json")
    if os.path.exists(fp):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def cache_set(key: str, value: Any):
    fp = os.path.join(CACHE_DIR, key + ".json")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)

def clean_text(s: str) -> str:
    s = re.sub(r"\s+", " ", s or "").strip()
    return s[:8000]  
