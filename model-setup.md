# Model Setup

## One-Time Online Steps

Run these before the conference venue or any offline rehearsal:

```bash
brew install ollama
ollama pull gemma4:e4b
```

If `ollama pull gemma4:e4b` fails, stop and fix that exact model tag. Do not replace it with another model.

## Offline Demo Steps

Start Ollama locally:

```bash
ollama serve
```

Or open the Ollama macOS app.

Then run the scripts from the repo root.

## Probe Results

Status: not yet measured in this execution environment.

- Model: `gemma4:e4b`
- Visible thinking probe: pending local run
- Single generation latency: pending local run
- Token/s: pending local run

Run this after the model is pulled:

```bash
python common/llm.py --probe
```

If the probe shows visible thinking, use Scenario 1's thinking-leak attack as the primary live narration. If not, use the three prompt-injection variants and fallback logs.
