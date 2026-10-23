import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .benchmark import run_benchmark, run_experiment
from .legacy import LANGUAGES, SUBSETS
from .llm_fallback import fallback_status, test_connection
from .rules import get_rules_report
from .transpiler import TARGETS, transpile


load_dotenv(Path(__file__).resolve().parent.parent / '.env')
logger = logging.getLogger(__name__)

app = FastAPI(title='Multi-Language Legacy Code Modernizer Prototype')
allowed_origins = [
    origin.strip()
    for origin in os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
    if origin.strip()
]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=['GET', 'POST'],
        allow_headers=['Content-Type'],
    )

FRONTEND = Path(__file__).resolve().parent.parent / 'frontend' / 'index.html'
FRONTEND_CONFIG = FRONTEND.parent / 'config.js'
MAX_SOURCE_CHARS = 50_000


class TranspileRequest(BaseModel):
    code: str = Field(min_length=1, max_length=MAX_SOURCE_CHARS)
    source_language: str = Field(default='Python-like', min_length=1, max_length=40)
    target_language: str = Field(default='JavaScript', min_length=1, max_length=40)


@app.get('/')
def home():
    return FileResponse(FRONTEND)


@app.get('/config.js')
def frontend_config():
    return FileResponse(FRONTEND_CONFIG, media_type='application/javascript')


@app.get('/languages')
def languages():
    return {'languages': LANGUAGES, 'subsets': SUBSETS, 'targets': TARGETS}


@app.get('/rules')
def rules_report():
    return {'ok': True, **get_rules_report()}


@app.get('/benchmark')
def benchmark(target: str = 'JavaScript'):
    if target not in TARGETS:
        raise HTTPException(status_code=422, detail='Unsupported target language.')
    return {'ok': True, **run_benchmark(target)}


@app.get('/experiment')
def experiment(target: str = 'JavaScript', repeats: int = 1, response: Response = None):
    if target not in TARGETS:
        if response is not None:
            response.status_code = 422
        return {'ok': False, 'error': 'Unsupported target language.'}
    if repeats < 1 or repeats > 10:
        if response is not None:
            response.status_code = 422
        return {'ok': False, 'error': 'Repeats must be between 1 and 10.'}
    return {'ok': True, **run_experiment(target, repeats=repeats)}


@app.get('/llm/status')
def llm_status():
    return {'ok': True, **fallback_status()}


@app.post('/llm/test')
def llm_test():
    try:
        result = test_connection()
        return {'ok': bool(result.get('ok')), **result}
    except Exception:
        logger.exception('LLM connectivity check failed')
        return {
            'ok': False,
            'error': 'LLM connectivity check failed. Check the server logs for details.',
            'status': fallback_status(),
        }


@app.post('/transpile')
def do_transpile(request: TranspileRequest):
    if request.source_language not in LANGUAGES:
        raise HTTPException(status_code=422, detail='Unsupported source language.')
    if request.target_language not in TARGETS:
        raise HTTPException(status_code=422, detail='Unsupported target language.')
    try:
        return {
            'ok': True,
            **transpile(request.code, request.source_language, request.target_language),
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        logger.exception('Translation failed')
        raise HTTPException(
            status_code=500,
            detail='Translation failed. Check the server logs for details.',
        ) from None
