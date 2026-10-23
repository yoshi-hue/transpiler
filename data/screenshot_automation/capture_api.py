import backend.main as main
import backend.benchmark as benchmark
from backend.transpiler import transpile as _transpile

def _no_external_llm(source, source_language="Python-like", target_language="JavaScript", **kwargs):
    kwargs["enable_llm"] = False
    return _transpile(source, source_language, target_language, **kwargs)

main.transpile = _no_external_llm
benchmark.transpile = _no_external_llm
app = main.app
