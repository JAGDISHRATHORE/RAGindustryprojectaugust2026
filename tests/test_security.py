import yaml
from conftest import ROOT

from complyrag.security import injection, pii


def test_injection_detector_on_labelled_cases():
    cases = yaml.safe_load((ROOT / "eval/gold/injection_cases.yaml").read_text())["cases"]
    wrong = [c["text"] for c in cases if injection.check(c["text"]).flagged != c["label"]]
    assert not wrong


def test_vendor_document_is_quarantined_at_ingestion(index):
    chunk = index.chunks["NWK-VQ-2026-14#s2"]
    assert chunk.quarantined
    assert "NWK-VQ-2026-14#s2" in index.manifest["quarantined"]
    # The harmless sections of the same document stay usable.
    assert not index.chunks["NWK-VQ-2026-14#s1"].quarantined


def test_redaction_of_structured_identifiers():
    text = (
        "Owner: Dr. Lena Hoffmann (lena.hoffmann@bank.example, +49 69 5550 1234). "
        "Payout to DE89 3704 0044 0532 0130 00."
    )
    result = pii.redact(text)
    for leaked in ("Lena", "Hoffmann", "@bank.example", "5550", "DE89"):
        assert leaked not in result.text
    assert result.counts == {"EMAIL": 1, "IBAN": 1, "PHONE": 1, "PERSON": 1}


def test_no_personal_data_reaches_the_index(index):
    blob = "\n".join(c.text for c in index.chunks.values())
    for leaked in ("lena.hoffmann", "Jonas Becker", "Markus Weber", "DE89 3704", "5550 1234"):
        assert leaked not in blob


def test_regulation_text_is_not_flagged(index):
    assert not [c for c in index.chunks.values() if c.source == "regulation" and c.flags]
