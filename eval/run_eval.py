"""Evaluation harness.

Three experiments, all scored against eval/gold/labels.yaml:

1. Retrieval ablation   BM25 vs dense vs hybrid, with and without the scope
                        filter: recall@k, MRR and contamination (share of
                        retrieved passages that belong to another AI system).
2. Distractor study     end-to-end verdicts for three set-ups that differ only
                        in how they handle look-alike evidence from FraudGuard:
                          naive      no scope filter, no citation scope check
                          verifier   no scope filter, citation check on
                          full       scope filter and citation check
                        The key number is "false covered": obligations with a
                        real gap that the system reports as compliant.
3. Guardrails           precision and recall of the prompt-injection detector.

Usage:
    python eval/run_eval.py --embedding lsa --reranker none --judge rules
    python eval/run_eval.py --embedding fastembed --reranker cross-encoder --judge llm
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from complyrag.agents.planner import ChecklistPlanner  # noqa: E402
from complyrag.config import Settings  # noqa: E402
from complyrag.index import build_index  # noqa: E402
from complyrag.obligations import applicability  # noqa: E402
from complyrag.pipeline import ComplianceAssessor  # noqa: E402
from complyrag.retrieval.rerank import make_reranker  # noqa: E402
from complyrag.retrieval.retriever import HybridRetriever, Scope  # noqa: E402
from complyrag.security import injection  # noqa: E402

GOLD = yaml.safe_load((ROOT / "eval/gold/labels.yaml").read_text())["labels"]
LABELS = ["covered", "partial", "gap", "not_applicable"]


# --------------------------------------------------------------------------- metrics
def macro_f1(pairs: list[tuple[str, str]]) -> float:
    scores = []
    for label in LABELS:
        tp = sum(p == label and g == label for g, p in pairs)
        fp = sum(p == label and g != label for g, p in pairs)
        fn = sum(p != label and g == label for g, p in pairs)
        if tp + fp + fn == 0:
            continue
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        scores.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return sum(scores) / len(scores)


def confusion(pairs: list[tuple[str, str]]) -> dict[str, dict[str, int]]:
    counts = Counter(pairs)
    return {g: {p: counts[(g, p)] for p in LABELS} for g in LABELS}


# --------------------------------------------------------------------------- experiments
def retrieval_ablation(settings: Settings, index, assessor: ComplianceAssessor) -> list[dict]:
    planner = ChecklistPlanner()
    profile = assessor.default_profile()
    rows = []
    reranker_names = ["none"]
    if settings.reranker_backend != "none":
        reranker_names.append(settings.reranker_backend)

    for rr_name in reranker_names:
        reranker = make_reranker(rr_name, settings.reranker_model)
        for mode in ("sparse", "dense", "hybrid"):
            if rr_name != "none" and mode != "hybrid":
                continue
            retriever = HybridRetriever(index, reranker, mode=mode)
            for scoped in (False, True):
                scope = Scope(systems=profile.evidence_scope if scoped else None)
                recalls, rrs, contamination, traps = [], [], [], 0
                for ob in assessor.obligations:
                    gold = GOLD[ob.id]
                    if not applicability(ob, profile)[0] or not gold.get("evidence"):
                        continue
                    k = min(10, max(settings.top_k, len(ob.checklist)))
                    result = retriever.retrieve(planner.initial(ob), scope, k)
                    hits = [e.chunk_id for e in result.evidence]
                    relevant = set(gold["evidence"])
                    recalls.append(len(relevant & set(hits)) / len(relevant))
                    first = next((i for i, h in enumerate(hits, 1) if h in relevant), None)
                    rrs.append(1 / first if first else 0.0)
                    in_scope = set(profile.evidence_scope)
                    foreign = [h for h in hits if index.chunks[h].system not in in_scope]
                    contamination.append(len(foreign) / len(hits) if hits else 0.0)
                    traps += bool(set(gold.get("trap", [])) & set(hits))
                rows.append(
                    {
                        "retrieval": mode,
                        "reranker": rr_name,
                        "scope_filter": scoped,
                        "recall@k": round(sum(recalls) / len(recalls), 3),
                        "mrr": round(sum(rrs) / len(rrs), 3),
                        "contamination": round(sum(contamination) / len(contamination), 3),
                        "trap_hits": traps,
                        "n": len(recalls),
                    }
                )
    return rows


def verdict_study(settings: Settings, index) -> list[dict]:
    setups = {
        "naive": dict(enforce_scope=False, verifier_scope=False),
        "verifier": dict(enforce_scope=False, verifier_scope=True),
        "full": dict(enforce_scope=True, verifier_scope=True),
    }
    rows = []
    for name, opts in setups.items():
        s = settings.model_copy(update={"enforce_scope": opts["enforce_scope"]})
        assessor = ComplianceAssessor(s, index=index)
        profile = assessor.default_profile()
        if not opts["verifier_scope"]:
            profile = profile.model_copy(update={"evidence_scope": []})
        started = time.perf_counter()
        report = assessor.run(profile=profile, max_workers=4)
        elapsed = time.perf_counter() - started

        pairs = [(GOLD[a.obligation_id]["verdict"], a.verdict.value) for a in report.assessments]
        false_covered = [
            a.obligation_id
            for a in report.assessments
            if a.verdict.value == "covered"
            and GOLD[a.obligation_id]["verdict"] in ("partial", "gap")
        ]
        missing_total = missing_found = 0
        for a in report.assessments:
            expected = set(GOLD[a.obligation_id].get("missing", []))
            missing_total += len(expected)
            missing_found += len(expected & set(a.missing_items))
        rows.append(
            {
                "setup": name,
                "accuracy": round(sum(g == p for g, p in pairs) / len(pairs), 3),
                "macro_f1": round(macro_f1(pairs), 3),
                "false_covered": false_covered,
                "gap_item_recall": round(missing_found / missing_total, 3),
                "flagged_for_review": sum(a.needs_human_review for a in report.assessments),
                "llm_calls": report.metrics.llm_calls,
                "tokens": report.metrics.prompt_tokens + report.metrics.completion_tokens,
                "seconds": round(elapsed, 1),
                "confusion": confusion(pairs),
                "errors": {
                    a.obligation_id: f"{GOLD[a.obligation_id]['verdict']} -> {a.verdict.value}"
                    for a in report.assessments
                    if a.verdict.value != GOLD[a.obligation_id]["verdict"]
                },
            }
        )
    return rows


def guardrail_eval() -> dict:
    cases = yaml.safe_load((ROOT / "eval/gold/injection_cases.yaml").read_text())["cases"]
    tp = sum(injection.check(c["text"]).flagged and c["label"] for c in cases)
    fp = sum(injection.check(c["text"]).flagged and not c["label"] for c in cases)
    fn = sum(not injection.check(c["text"]).flagged and c["label"] for c in cases)
    return {
        "cases": len(cases),
        "precision": round(tp / (tp + fp), 3) if tp + fp else 0.0,
        "recall": round(tp / (tp + fn), 3) if tp + fn else 0.0,
    }


# --------------------------------------------------------------------------- report
def to_markdown(config: dict, retrieval: list[dict], verdicts: list[dict], guard: dict) -> str:
    out = [
        f"# Evaluation results ({config['embedding']}, reranker {config['reranker']}, "
        f"judge {config['judge']})",
        "",
        f"Index `{config['index_version']}`, {config['date']}.",
        "",
        "## Retrieval",
        "",
        "| Retrieval | Reranker | Scope filter | Recall@k | MRR | Contamination | Trap hits |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in retrieval:
        out.append(
            f"| {r['retrieval']} | {r['reranker']} | {'on' if r['scope_filter'] else 'off'} | "
            f"{r['recall@k']:.3f} | {r['mrr']:.3f} | {r['contamination']:.3f} | "
            f"{r['trap_hits']} |"
        )
    out += [
        "",
        f"Computed over the {retrieval[0]['n']} applicable obligations that have gold "
        "evidence. Contamination is the share of retrieved passages from another AI system. "
        "Trap hits counts obligations where a FraudGuard passage that would wrongly close "
        "a gap made it into the evidence.",
        "",
        "## Verdicts and the distractor study",
        "",
        "| Set-up | Accuracy | Macro-F1 | False covered | Gap-item recall | Review flags |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for v in verdicts:
        fc = ", ".join(v["false_covered"]) or "none"
        out.append(
            f"| {v['setup']} | {v['accuracy']:.3f} | {v['macro_f1']:.3f} | {fc} | "
            f"{v['gap_item_recall']:.3f} | {v['flagged_for_review']} |"
        )
    out += ["", "Errors per set-up:", ""]
    for v in verdicts:
        errs = ", ".join(f"{k} ({e})" for k, e in v["errors"].items()) or "none"
        out.append(f"* {v['setup']}: {errs}")
    out += [
        "",
        "## Prompt-injection detector",
        "",
        f"{guard['cases']} labelled cases: precision {guard['precision']:.3f}, "
        f"recall {guard['recall']:.3f}.",
        "",
    ]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--embedding", default="lsa", choices=["lsa", "fastembed"])
    parser.add_argument("--reranker", default="none", choices=["none", "cross-encoder"])
    parser.add_argument("--judge", default="rules", choices=["rules", "llm"])
    parser.add_argument("--out", default=str(ROOT / "eval/results"))
    args = parser.parse_args()

    tmp = ROOT / ".eval_tmp"
    settings = Settings(
        data_dir=ROOT / "data",
        index_dir=tmp / "index",
        runs_dir=tmp / "runs",
        audit_log=tmp / "runs/audit.jsonl",
        embedding_backend=args.embedding,
        reranker_backend=args.reranker,
        judge_backend=args.judge,
    )
    index = build_index(settings, persist=False)
    assessor = ComplianceAssessor(settings, index=index)

    retrieval = retrieval_ablation(settings, index, assessor)
    verdicts = verdict_study(settings, index)
    guard = guardrail_eval()

    config = {
        "embedding": args.embedding,
        "reranker": args.reranker,
        "judge": args.judge if args.judge == "rules" else f"llm:{settings.llm_model}",
        "index_version": index.version,
        "date": time.strftime("%Y-%m-%d"),
    }
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{args.embedding}_{args.reranker}_{args.judge}"
    payload = {"config": config, "retrieval": retrieval, "verdicts": verdicts, "guardrails": guard}
    (out_dir / f"{stem}.json").write_text(json.dumps(payload, indent=2))
    (out_dir / f"{stem}.md").write_text(to_markdown(config, retrieval, verdicts, guard))
    print(to_markdown(config, retrieval, verdicts, guard))
    index.close()


if __name__ == "__main__":
    main()
