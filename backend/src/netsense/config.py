"""Filesystem locations shared by the API, capture library, and ML tools."""

import os
from pathlib import Path

# Editable installation resolves to the repository; deployments can override it.
PROJECT_ROOT = Path(os.environ.get("NETSENSE_HOME", Path(__file__).resolve().parents[3])).resolve()
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
SESSION_DB = DATA_DIR / "sessions.sqlite3"
TRAINING_DATA = DATA_DIR / "training" / "output1.csv"
SAMPLES_DIR = DATA_DIR / "samples"
