import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / 'data'
CORPUS_FILE = Path(os.getenv('VALIDATED_EXAMPLES_PATH', str(DATA_DIR / 'validated_examples.jsonl')))


def save_validated_example(source, target, ir, validation):
    """Keep successful translations as small reusable project reference data."""
    CORPUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {
        'source': source,
        'target': target,
        'ir': ir,
        'validation': validation,
    }
    with CORPUS_FILE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
