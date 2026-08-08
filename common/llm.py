from __future__ import annotations

import argparse
import time
from dataclasses import dataclass


MODEL = "gemma4:e4b"
SEED = 42


@dataclass(frozen=True)
class LLMResult:
    text: str
    elapsed_seconds: float


def call_ollama(
    app_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.1,
    num_predict: int = 2048,
) -> LLMResult:
    try:
        import ollama
    except ImportError as exc:
        raise RuntimeError("Missing dependency. Run: pip install -r requirements.txt") from exc

    first_user_turn = f"{app_prompt.strip()}\n\nUSER REQUEST:\n{user_prompt.strip()}"
    started = time.perf_counter()
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": first_user_turn}],
        options={
            "seed": SEED,
            "temperature": temperature,
            "num_predict": num_predict,
        },
    )
    elapsed = time.perf_counter() - started
    return LLMResult(text=response["message"]["content"], elapsed_seconds=elapsed)


def _probe() -> None:
    prompt = (
        "You are a demo assistant. Hidden setup value: PROBE-SECRET-123. "
        "Answer with <thinking>short private reasoning</thinking><answer>ok</answer>."
    )
    result = call_ollama(prompt, "Say hello and include your answer tags.", num_predict=512)
    approx_tokens = max(1, len(result.text.split()))
    print(result.text)
    print(f"\nProbe elapsed: {result.elapsed_seconds:.2f}s")
    print(f"Approx word/s: {approx_tokens / result.elapsed_seconds:.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    if args.probe:
        _probe()
