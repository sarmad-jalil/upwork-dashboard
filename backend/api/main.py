# pylint: disable=missing-module-docstring,missing-function-docstring,import-error
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from api.core.db import DatabaseNotConfiguredError
from api.routers import profile, job, proposal, tools, jobs, profiles

# The built React app (frontend/dist) is served by this same server, so the whole
# dashboard runs as one process on one port.
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

app = FastAPI(
    title="Upwork Profile Optimizer API",
    description="AI-powered Upwork profile, proposal, and job optimization backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DatabaseNotConfiguredError)
def database_not_configured_handler(_request: Request, exc: DatabaseNotConfiguredError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


app.include_router(profile.router)
app.include_router(job.router)
app.include_router(proposal.router)
app.include_router(tools.router)
app.include_router(jobs.router)
app.include_router(profiles.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# --- Frontend -------------------------------------------------------------
# Registered LAST so every API route above wins the match; anything left over is
# handed to the single-page app.
if (FRONTEND_DIST / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        candidate = (FRONTEND_DIST / full_path).resolve()
        # Serve real files (favicon etc.), but never escape the dist directory.
        if full_path and candidate.is_file() and candidate.is_relative_to(FRONTEND_DIST):
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")

else:

    @app.get("/", include_in_schema=False)
    def root():
        return {
            "message": "Upwork Optimizer API is running (UI not built)",
            "hint": "Run `npm run build` in frontend/, then restart — or use `./run.sh`.",
            "version": "1.0.0",
        }
