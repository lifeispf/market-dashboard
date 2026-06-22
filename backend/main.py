"""FastAPI entrypoint for the dashboard PoC.

Run from the workspace root:  uvicorn backend.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import health, market, sectors
from .store import db

app = FastAPI(title="Liquidity Ceiling Dashboard API", version="0.1.0-poc")

# Vite dev server origins (5173 default). Tighten for any non-local deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(market.router)
app.include_router(sectors.router)
app.include_router(health.router)


@app.on_event("startup")
def _startup():
    db.init_db()


@app.get("/")
def root():
    return {"service": "liquidity-ceiling-dashboard", "docs": "/docs", "health": "/api/health"}
