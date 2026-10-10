from pathlib import Path
from dotenv import load_dotenv

base = Path(__file__).resolve().parent
load_dotenv(base / '.env')

from backend.llm_fallback import fallback_status

status = fallback_status()
(base / 'llm_status_check.txt').write_text(str(status), encoding='utf-8')
print(f"configured={status['configured']} key_set={status['key_set']} endpoint_set={status['endpoint_set']} model={status['model']}")
