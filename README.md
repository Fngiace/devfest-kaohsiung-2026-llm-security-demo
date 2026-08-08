# Three Things You Should Do on Day 1 of Your LLM App

COSCUP 2026 demo repo for "你的 LLM App 上線第一天就該做的三件事".

This repo contains three offline, local-first demos that show an attack and a fix:

1. System prompt protection with `NemoClaw output_rail`
2. RAG source sanitization with `NemoClaw retrieval_rail`
3. Agent least privilege with `NemoClaw action_rail`

## Requirements

- macOS on Apple Silicon, tested target: MacBook Air M3, 16 GB RAM
- Python 3.11+
- Ollama running locally
- Model pulled before the live demo: `gemma4:e4b`

No cloud API is used by the demo scripts. The only network step is the one-time model pull described in [model-setup.md](model-setup.md).

## Setup

```bash
/opt/homebrew/bin/python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
ollama pull gemma4:e4b
```

Make sure the Ollama service is running before the demo. On macOS, opening the Ollama app is usually enough.

## Live Demo Order

Run each scenario as attack first, then defended:

```bash
python scenario1-systemprompt/attack.py
python scenario1-systemprompt/defended.py

python scenario2-rag/attack.py
python scenario2-rag/defended.py

python scenario3-agent-privilege/attack.py
python scenario3-agent-privilege/defended.py
```

Each script resets its own local state before running.

## Deterministic Checks

These checks use Python assertions and local replay fixtures. They do not call any grader model.

```bash
python scenario1-systemprompt/assert_check.py
python scenario2-rag/assert_check.py
python scenario3-agent-privilege/assert_check.py
```

## Fallback Logs

Pre-recorded terminal outputs live in `fallback-logs/`. If the model flakes during the talk, project those files and say they are outputs from the same scripts recorded earlier.

The fallback logs have been refreshed from a live local run with `gemma4:e4b` on 2026-08-08.

## Model Settings

The local Ollama wrapper uses:

- model: `gemma4:e4b`
- seed: `42`
- attack temperature: `0.7`
- defended temperature: `0.1`
- default `num_predict`: `2048`
- thinking/action scenarios may use `4096`
- measured probe latency: `32.65s`
- measured probe speed: `2.46` token/s

## Pending Fngi Review

- The implementation keeps `gemma4:e4b` as specified, with no automatic fallback to another model.
- Scenario 3 deletes only `./sandbox/customer_db.json`, recreated on every run.
- The optional combined scenario is intentionally not implemented until the three core scenarios are green.
- `gemma4:e4b` has been pulled on this machine. See `model-setup.md` for measured probe results.
