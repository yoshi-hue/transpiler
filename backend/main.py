from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from .transpiler import transpile, TARGETS
from .legacy import LANGUAGES, SUBSETS
from .benchmark import run_benchmark, run_experiment
from .llm_fallback import fallback_status, test_connection

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

app=FastAPI(title='Multi-Language Legacy Code Modernizer Prototype')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
FRONTEND=Path(__file__).resolve().parent.parent/'frontend'/'index.html'
FRONTEND_CONFIG=FRONTEND.parent/'config.js'
class TranspileRequest(BaseModel):
    code:str
    source_language:str='Python-like'
    target_language:str='JavaScript'
@app.get('/')
def home(): return FileResponse(FRONTEND)
@app.get('/config.js')
def frontend_config(): return FileResponse(FRONTEND_CONFIG, media_type='application/javascript')
@app.get('/languages')
def languages(): return {'languages':LANGUAGES,'subsets':SUBSETS,'targets':TARGETS}
@app.get('/benchmark')
def benchmark(target: str='JavaScript'):
    if target not in TARGETS: return {'ok':False,'error':'Unsupported target language.'}
    return {'ok':True,**run_benchmark(target)}

@app.get('/experiment')
def experiment(target: str='JavaScript', repeats: int=1):
    if target not in TARGETS: return {'ok':False,'error':'Unsupported target language.'}
    if repeats < 1 or repeats > 10: return {'ok':False,'error':'Repeats must be between 1 and 10.'}
    return {'ok':True,**run_experiment(target, repeats=repeats)}

@app.get('/llm/status')
def llm_status(): return {'ok':True, **fallback_status()}

@app.post('/llm/test')
def llm_test():
    try: return {'ok':True, **test_connection()}
    except Exception as exc: return {'ok':False, 'error':str(exc), 'status':fallback_status()}

@app.post('/transpile')
def do_transpile(request:TranspileRequest):
    if request.source_language not in LANGUAGES: return {'ok':False,'error':'Unsupported source language.'}
    try: return {'ok':True,**transpile(request.code,request.source_language,request.target_language)}
    except Exception as exc: return {'ok':False,'error':str(exc)}
