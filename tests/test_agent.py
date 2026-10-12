import pytest

from complyrag.agents.graph import AssessmentAgent
from complyrag.agents.judges import JudgeOutput, RuleJudge
from complyrag.agents.planner import ChecklistPlanner
from complyrag.llm.client import LLMClient, LLMOutputError
from complyrag.pipeline import ComplianceAssessor
from complyrag.retrieval.rerank import NoReranker
from complyrag.retrieval.retriever import HybridRetriever
from complyrag.schemas import ItemFinding, ItemStatus, Verdict


def test_offline_run_matches_answer_key(settings, index, gold):
    assessor = ComplianceAssessor(settings, index=index)
    report = assessor.run(max_workers=2)
    wrong = {
        a.obligation_id: (a.verdict.value, gold[a.obligation_id]["verdict"])
        for a in report.assessments
        if a.verdict.value != gold[a.obligation_id]["verdict"]
    }
    assert not wrong
    # Safety property: an item the documents do not support is never reported as met.
    # (The reverse can happen with the offline LSA embedder and is measured in eval/.)
    for a in report.assessments:
        expected_missing = set(gold[a.obligation_id].get("missing", []))
        assert expected_missing <= set(a.missing_items), a.obligation_id


def test_not_applicable_obligations_skip_retrieval(settings, index, obligations, profile):
    agent = AssessmentAgent(
        settings, HybridRetriever(index, NoReranker()), RuleJudge(), ChecklistPlanner()
    )
    result = agent.run(obligations["A14.5"], profile)
    assert result.verdict == Verdict.not_applicable
    assert result.retrieval_rounds == 0
    assert "annex_iii_1a_biometric" in result.rationale


class FlakyJudge:
    """Cites a passage it was never shown on the first try, then answers properly."""

    name = "stub"

    def __init__(self):
        self.calls = 0
        self.feedback = []

    def assess(self, obligation, profile, evidence, feedback=""):
        self.calls += 1
        self.feedback.append(feedback)
        if self.calls == 1:
            findings = [
                ItemFinding(
                    item_id=i.id, status=ItemStatus.met, evidence_ids=["MADE-UP#s1"], quote="x"
                )
                for i in obligation.checklist
            ]
            return JudgeOutput(findings=findings, rationale="first try", confidence=0.9)
        return RuleJudge().assess(obligation, profile, evidence)


def test_failed_citation_check_is_sent_back_to_the_judge(settings, index, obligations, profile):
    judge = FlakyJudge()
    agent = AssessmentAgent(
        settings, HybridRetriever(index, NoReranker()), judge, ChecklistPlanner()
    )
    result = agent.run(obligations["A12.1"], profile)
    assert judge.calls == 2
    assert "not retrieved" in judge.feedback[1]
    assert result.verdict == Verdict.covered
    assert result.assess_attempts == 2


class BrokenJudge:
    name = "broken"

    def assess(self, *args, **kwargs):
        raise TimeoutError("model endpoint unreachable")


def test_judge_failure_is_flagged_not_hidden(settings, index, obligations, profile):
    agent = AssessmentAgent(
        settings, HybridRetriever(index, NoReranker()), BrokenJudge(), ChecklistPlanner()
    )
    result = agent.run(obligations["A12.1"], profile)
    assert result.verdict != Verdict.covered
    assert result.needs_human_review
    assert any("judge failed" in r for r in result.review_reasons)


def test_gap_triggers_a_second_targeted_retrieval_round(settings, index, obligations, profile):
    agent = AssessmentAgent(
        settings, HybridRetriever(index, NoReranker()), RuleJudge(), ChecklistPlanner()
    )
    result = agent.run(obligations["A9.4"], profile)
    assert result.verdict == Verdict.gap
    assert result.retrieval_rounds == 2
    assert any(q.endswith("procedure documented") for q in result.queries)


def test_llm_client_repairs_invalid_json(settings, monkeypatch):
    client = LLMClient(settings.model_copy(update={"llm_cache": False}))
    answers = iter(
        [
            '{"findings": "not a list"}',
            '```json\n{"findings": [], "rationale": "ok", "confidence": 0.4}\n```',
        ]
    )
    seen = []

    def fake_complete(messages):
        seen.append(messages)
        return next(answers)

    monkeypatch.setattr(client, "_complete", fake_complete)
    out = client.complete_json("sys", "user", JudgeOutput)
    assert out.confidence == 0.4
    assert "did not match the required JSON schema" in seen[1][-1]["content"]


def test_llm_client_gives_up_after_retries(settings, monkeypatch):
    client = LLMClient(settings.model_copy(update={"llm_cache": False, "llm_json_retries": 1}))
    monkeypatch.setattr(client, "_complete", lambda messages: "no json here")
    with pytest.raises(LLMOutputError):
        client.complete_json("sys", "user", JudgeOutput)
