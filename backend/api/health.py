"""GET /api/health — key/auth availability so the UI can show graceful-degradation state."""
import os

from fastapi import APIRouter

from ..store import db

router = APIRouter()


@router.get("/api/health")
def health():
    db_ok = True
    try:
        db.query_latest_date("__healthcheck__")
    except Exception:
        db_ok = False
    return {
        "status": "ok",
        "db": db_ok,
        "fredKey": bool(os.environ.get("FRED_API_KEY")),
        "krxAuth": bool(
            os.environ.get("KRX_API_KEY")
            or (os.environ.get("KRX_ID") and os.environ.get("KRX_PW"))
        ),
    }
