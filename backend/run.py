"""
Convenience entrypoint for launching the AURA-Rx FastAPI Backend server.
Usage:
    python backend/run.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root directory to sys.path and load environment variables early
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env")

import uvicorn
from backend.app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    host = os.environ.get("HOST", settings.HOST)
    port = int(os.environ.get("PORT", settings.PORT))
    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        reload=settings.DEBUG,
    )

