import json
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def read(key, default=None):
    file = DATA_DIR / f"{key}.json"
    if file.exists():
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                # FIX: Ensure we return the correct type
                if default is None:
                    return data if isinstance(data, list) else []
                return data if isinstance(data, type(default)) else default
        except:
            return default if default is not None else []
    return default if default is not None else []

def write(key, data):
    file = DATA_DIR / f"{key}.json"
    with open(file, 'w') as f:
        json.dump(data, f, indent=2, default=str)