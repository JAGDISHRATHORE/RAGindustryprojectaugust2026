"""Gap report rendering (Markdown for people, JSON for systems)."""

from __future__ import annotations

from pathlib import Path

from complyrag.schemas import ItemStatus, RunReport, Verdict

_ICON = {
    Verdict.covered: "covered",
    Verdict.partial: "PARTIAL",
    Verdict.gap: "GAP",
    Verdict.not_applicable: "n/a",
}


def render_markdown(report: RunReport) -> str:
    counts = report.counts()
    applicable = len(report.assessments) - counts["not_applicable"]
    review = [a for a in report.assessments if a.needs_human_review]
    lines = [
        f"# EU AI Act gap assessment: {report.system.name}",
        "",
        f"Run `{report.run_id}`, {report.created_at:%Y-%m-%d %H:%M} UTC. "
        f"Judge `{report.judge}`, prompt `{report.prompt_version}`, "
        f"index `{report.index_version}`.",
        "",
        "> Generated automatically from the documents in scope. Every verdict cites its "
        "evidence. Items flagged for review must be checked by a qualified person before "
        "the report is used.",
        "",
        "## Summary",
        "",
        f"* Obligations assessed: {applicable} applicable, "
        f"{counts['not_applicable']} not applicable",
        f"* Covered: {counts['covered']}, partial: {counts['partial']}, gaps: {counts['gap']}",
        f"* Flagged for human review: {len(review)}",
        f"* Runtime {report.metrics.latency_s}s, {report.metrics.llm_calls} LLM calls, "
        f"{report.metrics.prompt_tokens + report.metrics.completion_tokens} tokens, "
        f"cost EUR {report.metrics.cost_eur:.4f}",
        "",
        "| Obligation | Requirement | Result | Confidence | Review |",
        "| --- | --- | --- | --- | --- |",
    ]
    for a in report.assessments:
        lines.append(
            f"| {a.reference} | {a.title} | {_ICON[a.verdict]} | {a.confidence:.2f} | "
            f"{'yes' if a.needs_human_review else ''} |"
        )

    lines += ["", "## Findings", ""]
    for a in report.assessments:
        if a.verdict == Verdict.not_applicable:
            continue
        lines += [f"### {a.reference}: {a.title}", "", f"**Result: {_ICON[a.verdict]}**", ""]
        lines += [a.rationale, ""]
        for f in a.findings:
            mark = {"met": "[x]", "not_met": "[ ]", "unclear": "[?]"}[f.status.value]
            detail = ""
            if f.status == ItemStatus.met and f.quote:
                detail = f' "{f.quote}" ({", ".join(f.evidence_ids)})'
            elif f.note:
                detail = f" ({f.note})"
            lines.append(f"- {mark} `{f.item_id}`{detail}")
        if a.remediation:
            lines += ["", f"Remediation: {a.remediation}"]
        if a.review_reasons:
            lines += ["", "Review needed because: " + "; ".join(a.review_reasons)]
        lines.append("")

    quarantined = sorted({c for a in report.assessments for c in a.quarantined_chunks})
    if quarantined:
        lines += [
            "## Quarantined content",
            "",
            "These passages looked like instructions aimed at an AI system. They were "
            "excluded from the evidence and should be checked by security:",
            "",
            *[f"- `{c}`" for c in quarantined],
            "",
        ]
    return "\n".join(lines)


def save(report: RunReport, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    md = out_dir / f"{report.run_id}.md"
    js = out_dir / f"{report.run_id}.json"
    md.write_text(render_markdown(report), encoding="utf-8")
    js.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return md, js
