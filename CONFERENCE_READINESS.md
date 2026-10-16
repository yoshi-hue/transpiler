# Conference-readiness summary

## Problem statement

Legacy software systems often contain older imperative languages such as COBOL, FORTRAN, Pascal, and BASIC. These systems are still operationally important, but migrating them to modern runtimes is costly, error-prone, and difficult to validate.

The central research problem is not simply translating syntax from one language to another. The harder problem is translating with confidence: preserve semantics under executable validation, avoid unsafe model hallucinations, and keep the pipeline explainable enough for engineering use.

## Contribution

This project proposes a hybrid transpilation pipeline with four main layers:

1. shared compiler front end and shared IR
2. deterministic rule-first translation for supported legacy constructs
3. scoped LLM fallback only for unsupported or risky constructs
4. executable validation and learned-rule accumulation to improve future reliability

This is a credible research narrative because it explicitly separates deterministic translation from probabilistic assistance and requires semantic evidence before accepting model-generated fragments.

## Why it is interesting

The system addresses a real engineering bottleneck: legacy modernization is expensive and risky, but much of the code is structurally repetitive and deterministic. That makes it well suited for rule-based compiler techniques, while unusual patterns benefit from model assistance.

The key insight is that AI can be most useful when constrained by validation and by the compiler architecture itself. The project therefore treats the LLM as a fallback component inside a disciplined pipeline rather than as a replacement for compiler semantics.

## Evaluation story

The project already includes a rule-only baseline and a hybrid run. For a more publication-ready story, the evaluation should explicitly include the full ablation chain:

- Rule-only baseline
- Rule-first + LLM fallback
- Rule-first + contracts + risk-based validation + learned rules

This is important because the value of the system is not just “translation happened,” but “translation was supported by evidence and validation.”

## Benchmark expectations

A strong benchmark for the project should include:

- arithmetic and assignment programs
- branching and comparison programs
- loops and control-flow cases
- unsupported syntax cases to quantify fallback behavior
- per-language and per-construct breakdowns
- median and mean LLM latency
- validation failure categories

## Current limitations

This is still a prototype. It is not a complete implementation of all COBOL, FORTRAN, Pascal, BASIC, or Python-like constructs. The validation layer is execution-based and empirical rather than formal verification, and the current benchmark remains intentionally compact.

These limitations are real, but they are also reasonable for a focused prototype. The project is strongest when positioned as a hybrid compiler research prototype with validation-first translation rather than as a broad language-coverage claim.

## Recommended framing for a conference or demo

The best framing is:

- hybrid compiler architecture
- reliability-first translation
- LLM fallback with validation gate
- learned rules and failure diagnosis

This framing makes the project feel both technically grounded and publication-aware.
