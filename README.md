# Multi-Language Legacy Code Modernizer

A compiler-design prototype implementing the project's final architecture:

**shared compiler front end → shared IR → rule-first translation → scoped LLM fallback → executable validation**

The prototype supports documented subsets of COBOL, FORTRAN, Pascal, BASIC, and the earlier Python-like language. JavaScript and Python are available as targets for the implemented subset.

## What makes the LLM integration meaningful

The model is not used as a whole-program black-box translator. The deterministic rule layer runs first. Only constructs outside the explicit rule coverage are sent to the external model. Every request is logged with a request ID, model, prompt version/hash, latency, retry count, and response status.

The LLM output remains a **candidate** until validation supports accepting it. This prevents a plausible-looking model response from being counted as a correct translation.

## Research-grade translation safeguards

The translator now emits a machine-readable semantic contract for each translation unit before it is accepted. This contract records inputs, output type, side effects, exception expectations, source/target API mappings, validation evidence, and a confidence score.

The system also computes a construct-level risk score and selects the validation policy accordingly. Low-risk constructs use direct rule-based validation, while medium and high-risk constructs trigger additional checks, generated test cases, and stricter review.

Validated LLM fallback fragments are accumulated into a learned rule set, so supported mappings grow over time and the system becomes less dependent on external model calls. Translation failures are also classified with a reusable failure fingerprint describing the stage, source construct, target mismatch, and suggested repair.

Together, these pieces create the project’s technical contribution:

```text
source code → semantic contract → risk-aware validation → learned rules → failure diagnosis
```

## Configure a real external model

Copy `.env.example` to `.env` and replace `LLM_API_KEY` with your Gemini API key. Do **not** commit the API key.

The default configuration uses Google's OpenAI-compatible Gemini endpoint:

```text
LLM_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
LLM_API_MODE=chat
LLM_PROVIDER=Google Gemini
LLM_MODEL=gemini-2.5-flash
LLM_API_KEY=<your Gemini API key>
```

OpenAI-compatible endpoints are also supported. The server accepts OpenAI Responses endpoints by setting `LLM_API_MODE=responses` and using the provider's `/v1/responses` URL.

If your provider requires extra headers, set `LLM_EXTRA_HEADERS` as JSON, for example:

```text
LLM_EXTRA_HEADERS={"HTTP-Referer":"https://localhost:8000","X-Title":"Mini Transpiler"}
```

The UI's **Test LLM connection** button makes a real request to the configured endpoint. It reports the model, request ID and latency without exposing the secret key.

## Run

```bash
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000`.

Node.js is required for JavaScript target execution; Python 3 is required for the Python target.

## Deploy as a live website with GitHub Pages

The repository includes a GitHub Actions workflow that publishes the static frontend from `frontend/` whenever you push to `main` or `master`. In the repository's **Settings → Pages**, set the build and deployment source to **GitHub Actions**. After the workflow succeeds, the site will be available at `https://yoshi-hue.github.io/transpiler/`.

GitHub Pages only hosts static files; it cannot run this project's Python/FastAPI backend. To enable translation, benchmarks, experiments, and LLM checks on the published site:

1. Deploy the FastAPI app (`backend.main:app`) to a Python-capable host.
2. Set `LLM_API_KEY` and any other LLM settings as environment variables on that host if you want LLM fallback. Never put the key in the frontend or GitHub Pages.
3. Set `window.TRANSPILER_API_BASE_URL` in [`frontend/config.js`](./frontend/config.js) to the backend's public origin (for example, `https://your-backend.example.com`), then push the change. Do not include an API path or trailing slash.

The frontend and backend can still be run together locally using the instructions above; leave the API URL empty in `frontend/config.js` in that case.

## Evaluation

Run the in-project benchmark from the UI or:

```text
GET /benchmark?target=JavaScript
```

For a research evaluation, compare the same benchmark under two conditions:
1. rule-only baseline
2. rule-first + configured LLM fallback
3. rule-first + contracts + risk-aware validation + learned rules

Keep the model, prompt version, temperature, benchmark, runtime, and rule table fixed. See `LLM_EVALUATION.md` for the recommended protocol.

## Scope

This is a research/course prototype, not a full implementation of COBOL, FORTRAN, Pascal, BASIC, or any other language. Results only apply to the documented subsets and tested constructs. Execution-based validation is empirical I/O validation over the supplied test cases; it is not a formal proof of program equivalence.
