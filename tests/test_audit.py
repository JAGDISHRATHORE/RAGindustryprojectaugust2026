import json

from complyrag.observability.audit import AuditLog, verify_chain


def test_chain_detects_tampering(tmp_path):
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path)
    for verdict in ("covered", "gap", "partial"):
        log.append("assessment", {"verdict": verdict})
    assert verify_chain(path) == (True, 3)

    lines = path.read_text().splitlines()
    record = json.loads(lines[1])
    record["payload"]["verdict"] = "covered"  # someone "fixes" a gap after the fact
    lines[1] = json.dumps(record, sort_keys=True)
    path.write_text("\n".join(lines) + "\n")
    assert verify_chain(path) == (False, 1)
