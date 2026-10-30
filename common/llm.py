from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path


def _client():
    import ollama
    return ollama.Client(host="http://localhost:11434", trust_env=False, timeout=900)


def _record(response, elapsed, *, content=None, thinking=None):
    target = os.environ.get("DEVFEST_TRACE")
    if not target:
        return
    data = response.model_dump(mode="json") if hasattr(response, "model_dump") else dict(response)
    if content is not None:
        data.setdefault("message", {})["content"] = content
    if thinking is not None:
        data.setdefault("message", {})["thinking"] = thinking
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"elapsed_seconds": elapsed, "response": data}, ensure_ascii=False) + "\n")


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
    response = _client().chat(
        model=MODEL,
        messages=[{"role": "user", "content": first_user_turn}],
        options={
            "seed": SEED,
            "temperature": temperature,
            "num_predict": num_predict,
        },
    )
    elapsed = time.perf_counter() - started
    _record(response, elapsed)
    eval_duration_ns = response.get("eval_duration")
    return LLMResult(
        text=response["message"]["content"],
        elapsed_seconds=elapsed,
        eval_count=response.get("eval_count"),
        eval_duration_seconds=eval_duration_ns / 1_000_000_000 if eval_duration_ns else None,
    )


def call_ollama_streaming(
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
    parts: list[str] = []
    thinking_parts: list[str] = []
    final_chunk = None
    for chunk in _client().chat(
        model=MODEL,
        messages=[{"role": "user", "content": first_user_turn}],
        options={
            "seed": SEED,
            "temperature": temperature,
            "num_predict": num_predict,
        },
        stream=True,
    ):
        final_chunk = chunk
        content = chunk.get("message", {}).get("content", "")
        thinking_parts.append(chunk.get("message", {}).get("thinking", "") or "")
        if content:
            print(content, end="", flush=True)
            parts.append(content)

    elapsed = time.perf_counter() - started
    if final_chunk is not None:
        _record(final_chunk, elapsed, content="".join(parts), thinking="".join(thinking_parts))
    print(flush=True)
    eval_duration_ns = final_chunk.get("eval_duration") if final_chunk else None
    return LLMResult(
        text="".join(parts),
        elapsed_seconds=elapsed,
        eval_count=final_chunk.get("eval_count") if final_chunk else None,
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
