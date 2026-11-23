# Submission report — Product Strategist

## Architecture
The IDE agent orchestrates the workflow; Python tools perform deterministic validation, calculation and bookkeeping. Persistent rules live in `AGENTS.md`, repeatable procedures in `skills/`, reference methods in `knowledge/`, current state in `state/`, and deliverables in `artifacts/`.

## Demo
The demo follows the supplied PDF brief for a fictional mobile operator. It covers family data-package assistance and assistance for owners of multiple own numbers.

The repository contains an adapted brief, synthetic targets and scenarios, an evidence graph, four alternatives, a product strategy, a communication strategy, a validation plan, a quarterly plan, a three-year indicator and a decision recheck mechanism.

## Implemented features
- Human approval checkpoints and resumable workflow state.
- Source tracing and separation of facts, hypotheses and forecasts.
- Independent adversarial review.
- Synthetic respondents, limited to hypothesis generation.
- UX, data-analysis and decision-follow-up skills.
- Fetch MCP and Cursor hooks.
- CLI validation and recheck tools.
- Retention of provenance and source hashes.

## Evidence boundaries
The demo uses only synthetic and authorized inputs. It does not prove real demand or real operator economics. A real experiment, customer contact or external commitment requires separate human approval.

## Models and services
No specific model or provider is hard-coded. The IDE agent/model is selected by the user. Deterministic Python tools use the standard library and require no API key or paid service. Provider cost and token telemetry must be recorded in a real paired run.
