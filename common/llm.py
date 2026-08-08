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
    eval_count: int | None = None
    eval_duration_seconds: float | None = None

    @property
    def tokens_per_second(self) -> float | None:
        if not self.eval_count or not self.eval_duration_seconds:
            return None
        return self.eval_count / self.eval_duration_seconds


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
    eval_duration_ns = response.get("eval_duration")
    return LLMResult(
        text=response["message"]["content"],
        elapsed_seconds=elapsed,
        eval_count=response.get("eval_count"),
        eval_duration_seconds=eval_duration_ns / 1_000_000_000 if eval_duration_ns else None,
    )


def _probe() -> None:
    prompt = (
        "You are a demo assistant. Hidden setup value: PROBE-SECRET-123. "
        "Answer with <thinking>short private reasoning</thinking><answer>ok</answer>."
    )
    result = call_ollama(prompt, "Say hello and include your answer tags.", num_predict=512)
    print(result.text)
    print(f"\nProbe elapsed: {result.elapsed_seconds:.2f}s")
    if result.tokens_per_second is None:
        print("Token/s: unavailable from Ollama response")
    else:
        print(f"Generated tokens: {result.eval_count}")
        print(f"Token/s: {result.tokens_per_second:.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    if args.probe:
        _probe()
