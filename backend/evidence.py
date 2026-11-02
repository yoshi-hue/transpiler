"""Immutable, content-addressed evidence records for local evaluations."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import uuid


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_evidence(*, output_dir, command, settings, outcomes, files=(), runtime=None):
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    record = {
        'schema_version': '1.0',
        'run_id': run_id,
        'timestamp_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'command': command,
        'settings': settings,
        'runtime': runtime or {},
        'inputs': {str(Path(path)): sha256_bytes(Path(path).read_bytes()) for path in files},
        'outcomes': outcomes,
    }
    path = root / f'{run_id}.json'
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='')
    return path, record
