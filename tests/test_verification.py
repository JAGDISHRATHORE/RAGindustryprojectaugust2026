from complyrag.agents.judges import aggregate_verdict
from complyrag.agents.verification import quote_in_text, verify
from complyrag.schemas import Evidence, ItemFinding, ItemStatus, Verdict


def _ev(chunk_id, text, system="creditlens"):
    return Evidence(
        chunk_id=chunk_id,
        doc_id=chunk_id.split("#")[0],
        title="t",
        section="s",
        system=system,
        text=text,
        retrieval_score=0.1,
    )


EVIDENCE = [
    _ev(
        "NWK-RUN-022#s2",
        "Every scoring request is logged automatically by the scoring service "
        "for the whole lifetime of the system.",
    ),
    _ev(
        "NWK-MC-FG-03#s2",
        "Analysts can halt FraudGuard with the pause scoring switch.",
        system="fraudguard",
    ),
]


def test_quote_matching_tolerates_case_whitespace_and_ellipsis():
    text = EVIDENCE[0].text
    assert quote_in_text("every scoring request is  LOGGED automatically", text)
    assert quote_in_text("Every scoring request ... whole lifetime of the system", text)
    assert not quote_in_text("requests are logged manually", text)
    assert not quote_in_text("", text)


def test_valid_findings_pass(obligations, profile):
    findings = [
        ItemFinding(
            item_id="automatic_logging",
            status=ItemStatus.met,
            evidence_ids=["NWK-RUN-022#s2"],
            quote="is logged automatically",
        ),
        ItemFinding(
            item_id="lifetime",
            status=ItemStatus.met,
            evidence_ids=["NWK-RUN-022#s2"],
            quote="for the whole lifetime of the system",
        ),
    ]
    result = verify(obligations["A12.1"], profile, findings, EVIDENCE)
    assert result.ok and result.verified_met == 2


def test_invented_quote_is_rejected(obligations, profile):
    findings = [
        ItemFinding(
            item_id="automatic_logging",
            status=ItemStatus.met,
            evidence_ids=["NWK-RUN-022#s2"],
            quote="logs are kept forever in the cloud",
        ),
        ItemFinding(item_id="lifetime", status=ItemStatus.not_met),
    ]
    result = verify(obligations["A12.1"], profile, findings, EVIDENCE)
    assert not result.ok
    assert result.findings[0].status == ItemStatus.unclear


def test_citation_of_unretrieved_passage_is_rejected(obligations, profile):
    findings = [
        ItemFinding(
            item_id="automatic_logging",
            status=ItemStatus.met,
            evidence_ids=["NWK-XYZ#s9"],
            quote="logged",
        ),
        ItemFinding(item_id="lifetime", status=ItemStatus.not_met),
    ]
    result = verify(obligations["A12.1"], profile, findings, EVIDENCE)
    assert any("not retrieved" in p for p in result.problems)


def test_evidence_from_another_system_is_rejected(obligations, profile):
    findings = [
        ItemFinding(
            item_id="stop",
            status=ItemStatus.met,
            evidence_ids=["NWK-MC-FG-03#s2"],
            quote="pause scoring switch",
        ),
    ]
    result = verify(obligations["A14.4"], profile, findings, EVIDENCE)
    assert any("different AI system" in p for p in result.problems)
    stop = next(f for f in result.findings if f.item_id == "stop")
    assert stop.status == ItemStatus.unclear


def test_skipped_items_are_reported(obligations, profile):
    result = verify(obligations["A14.4"], profile, [], EVIDENCE)
    assert len(result.problems) == len(obligations["A14.4"].checklist)


def test_verdict_is_derived_from_items(obligations):
    ob = obligations["A12.1"]
    met = ItemFinding(item_id="automatic_logging", status=ItemStatus.met)
    no = ItemFinding(item_id="lifetime", status=ItemStatus.not_met)
    unclear = ItemFinding(item_id="lifetime", status=ItemStatus.unclear)
    assert (
        aggregate_verdict(ob, [met, met.model_copy(update={"item_id": "lifetime"})])
        == Verdict.covered
    )
    assert aggregate_verdict(ob, [met, no]) == Verdict.partial
    assert (
        aggregate_verdict(ob, [no.model_copy(update={"item_id": "automatic_logging"}), no])
        == Verdict.gap
    )
    # "unclear" is never silently turned into a gap.
    assert (
        aggregate_verdict(ob, [no.model_copy(update={"item_id": "automatic_logging"}), unclear])
        == Verdict.partial
    )
