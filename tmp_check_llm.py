from pathlib import Path
import os

for line in Path('.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    key, value = line.split('=', 1)
    os.environ[key] = value

from backend.llm_fallback import fallback_status, test_connection

print(fallback_status())
print(test_connection())
