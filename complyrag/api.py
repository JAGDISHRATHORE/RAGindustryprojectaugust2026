"""REST API.

    GET  /health                       liveness and index version
    POST /index                        rebuild the index from the data folder
    POST /search                       hybrid search inside a scope (debugging, UI)
    POST /assessments                  run a gap assessment
    GET  /assessments/{run_id}         stored result as JSON
    GET  /assessments/{run_id}/report  stored result as Markdown

Assessments run synchronously, which is fine for one system with about 30
obligations. For many systems the next step is a job queue (Celery or Azure
Service Bus) with the same request schema.
"""

from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from complyrag import __version__, reporting
from complyrag.config import Settings, get_settings
from complyrag.index import build_index
from complyrag.pipeline import ComplianceAssessor
from complyrag.retrieval.retriever import Scope
from complyrag.schemas import RunReport, SystemProfile
from complyrag.security import injection

log = logging.getLogger(__name__)


class _State:
    assessor: ComplianceAssessor | None = None
    lock = threading.Lock()


state = _State()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    state.assessor = ComplianceAssessor(settings)
    yield
    if state.assessor:
        state.assessor.close()


app = FastAPI(title="ComplyRAG", version=__version__, lifespan=lifespan)


def require_key(
    x_api_key: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_settings),
) -> None:
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="invalid or missing API key")


def assessor() -> ComplianceAssessor:
    if state.assessor is None:
        raise HTTPException(status_code=503, detail="service is starting")
    return state.assessor


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    systems: list[str] | None = None


class AssessmentRequest(BaseModel):
    profile: SystemProfile | None = None
    obligation_ids: list[str] | None = None


@app.get("/health")
def health() -> dict:
    a = state.assessor
    return {
        "status": "ok" if a else "starting",
        "version": __version__,
        "index_version": a.index.version if a else None,
        "judge": a.judge.name if a else None,
    }


@app.post("/index", dependencies=[Depends(require_key)])
def rebuild_index(settings: Settings = Depends(get_settings)) -> dict:
    with state.lock:
        if state.assessor:
            state.assessor.close()
        state.assessor = ComplianceAssessor(settings, index=build_index(settings))
        return state.assessor.index.manifest


@app.post("/search", dependencies=[Depends(require_key)])
def search(req: SearchRequest, a: ComplianceAssessor = Depends(assessor)) -> dict:
    check = injection.check(req.query)
    if check.flagged:
        raise HTTPException(status_code=400, detail="query rejected by input guardrail")
    result = a.retriever.retrieve([req.query], Scope(systems=req.systems), top_k=req.top_k)
    return {
        "results": [e.model_dump() for e in result.evidence],
        "quarantined": result.quarantined,
    }


@app.post("/assessments", dependencies=[Depends(require_key)])
def create_assessment(
    req: AssessmentRequest,
    a: ComplianceAssessor = Depends(assessor),
    settings: Settings = Depends(get_settings),
) -> RunReport:
    known = {o.id for o in a.obligations}
    unknown = [o for o in (req.obligation_ids or []) if o not in known]
    if unknown:
        raise HTTPException(status_code=422, detail=f"unknown obligation ids: {unknown}")
    report = a.run(profile=req.profile, obligation_ids=req.obligation_ids)
    reporting.save(report, settings.runs_dir)
    return report


def _load(run_id: str, suffix: str, settings: Settings) -> str:
    if not run_id.replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail="invalid run id")
    path = settings.runs_dir / f"{run_id}.{suffix}"
    if not path.exists():
        raise HTTPException(status_code=404, detail="run not found")
    return path.read_text(encoding="utf-8")


@app.get("/assessments/{run_id}", dependencies=[Depends(require_key)])
def get_assessment(run_id: str, settings: Settings = Depends(get_settings)) -> RunReport:
    return RunReport.model_validate_json(_load(run_id, "json", settings))


@app.get(
    "/assessments/{run_id}/report",
    response_class=PlainTextResponse,
    dependencies=[Depends(require_key)],
)
def get_report(run_id: str, settings: Settings = Depends(get_settings)) -> str:
    return _load(run_id, "md", settings)
