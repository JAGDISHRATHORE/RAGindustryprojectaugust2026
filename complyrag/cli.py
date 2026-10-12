"""Command line interface: `complyrag index | assess | search | serve | verify-audit`."""

from __future__ import annotations

import json
import logging
from typing import Annotated

import typer

from complyrag import reporting
from complyrag.config import get_settings

app = typer.Typer(add_completion=False, help="EU AI Act gap analysis with agentic RAG.")


@app.callback()
def _setup(verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else get_settings().log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@app.command()
def index() -> None:
    """Parse, redact, screen and index the documents."""
    from complyrag.index import build_index

    idx = build_index(get_settings())
    typer.echo(json.dumps(idx.manifest, indent=2))
    idx.close()


@app.command()
def assess(
    obligation: Annotated[list[str] | None, typer.Option("--obligation", "-o")] = None,
    workers: int = 4,
) -> None:
    """Run the gap assessment and write Markdown and JSON reports."""
    from complyrag.pipeline import ComplianceAssessor

    settings = get_settings()
    assessor = ComplianceAssessor(settings)
    try:
        report = assessor.run(obligation_ids=obligation, max_workers=workers)
    finally:
        assessor.close()
    md, js = reporting.save(report, settings.runs_dir)
    counts = report.counts()
    typer.echo(
        f"{report.run_id}: covered={counts['covered']} partial={counts['partial']} "
        f"gap={counts['gap']} n/a={counts['not_applicable']} "
        f"review={sum(a.needs_human_review for a in report.assessments)}"
    )
    typer.echo(f"report: {md}\njson:   {js}")


@app.command()
def search(query: str, top_k: int = 5, all_systems: bool = False) -> None:
    """Search the index the way the agent does (useful for debugging retrieval)."""
    from complyrag.pipeline import ComplianceAssessor
    from complyrag.retrieval.retriever import Scope

    assessor = ComplianceAssessor(get_settings())
    try:
        profile = assessor.default_profile()
        scope = Scope(systems=None if all_systems else profile.evidence_scope)
        result = assessor.retriever.retrieve([query], scope, top_k=top_k)
    finally:
        assessor.close()
    for e in result.evidence:
        typer.echo(f"{e.chunk_id:<24} {e.system:<11} {e.section}")
    if result.quarantined:
        typer.echo(f"quarantined: {result.quarantined}")


@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start the REST API."""
    import uvicorn

    uvicorn.run("complyrag.api:app", host=host, port=port)


@app.command("verify-audit")
def verify_audit() -> None:
    """Check that the audit log has not been modified."""
    from complyrag.observability.audit import verify_chain

    ok, n = verify_chain(get_settings().audit_log)
    typer.echo(f"{'valid' if ok else 'BROKEN'} chain, {n} verified records")
    raise typer.Exit(0 if ok else 1)


if __name__ == "__main__":
    app()
