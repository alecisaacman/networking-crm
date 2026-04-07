from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = PROJECT_ROOT / "runtime"
STATE_DIR = RUNTIME_DIR / "state"
LOGS_DIR = RUNTIME_DIR / "logs"
ARTIFACTS_DIR = RUNTIME_DIR / "artifacts"
CONFIG_DIR = PROJECT_ROOT / "config"
DB_PATH = STATE_DIR / "networking.db"
SCHEMA_PATH = CONFIG_DIR / "schema.sql"
