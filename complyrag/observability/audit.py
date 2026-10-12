"""Append-only, hash-chained audit log.

Each record stores the hash of the previous record. If anybody edits or
deletes a line later, `verify_chain` fails from that point on. That gives
auditors the tamper evidence they expect from a system whose output feeds a
regulatory file, without needing a database.
"""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime
from pathlib import Path

GENESIS = "0" * 64


class AuditLog:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _last_hash(self) -> str:
        if not self.path.exists():
            return GENESIS
        last = ""
        with self.path.open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    last = line
        return json.loads(last)["hash"] if last else GENESIS

    def append(self, event: str, payload: dict) -> str:
        with self._lock:
            record = {
                "ts": datetime.now(UTC).isoformat(),
                "event": event,
                "payload": payload,
                "prev_hash": self._last_hash(),
            }
            body = json.dumps(record, sort_keys=True, default=str)
            record["hash"] = hashlib.sha256(body.encode()).hexdigest()
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, sort_keys=True, default=str) + "\n")
            return record["hash"]


def verify_chain(path: Path) -> tuple[bool, int]:
    """Return (is_valid, number_of_valid_records)."""
    prev = GENESIS
    count = 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            record = json.loads(line)
            claimed = record.pop("hash")
            if record["prev_hash"] != prev:
                return False, count
            body = json.dumps(record, sort_keys=True, default=str)
            if hashlib.sha256(body.encode()).hexdigest() != claimed:
                return False, count
            prev, count = claimed, count + 1
    return True, count
