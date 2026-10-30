"""Demonstration scanner: lexical normalization, one-level base64/hex decoding.

Offsets are half-open Python character offsets in the original input. Encoded
findings point to the complete encoded token, not invented decoded-text offsets.
Translation, paraphrase and recursive/fragmented encodings remain out of scope.
"""
from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class Finding:
    canary: str
    start: int
    end: int
    transformations: tuple[str, ...]


def _stages(text: str):
    spans = [(i, i + 1) for i in range(len(text))]
    yield text, spans, ()
    transformed, mapped = [], []
    i = 0
    while i < len(text):
        j = i + 1
        while j < len(text) and unicodedata.combining(text[j]):
            j += 1
        part = unicodedata.normalize("NFKC", text[i:j])
        transformed.extend(part)
        mapped.extend([(i, j)] * len(part))
        i = j
    text, spans = "".join(transformed), mapped
    steps = ("NFKC",)
    yield text, spans, steps
    for name, operation in (
        ("remove_zero_width", lambda c: "" if unicodedata.category(c) == "Cf" or c in "\ufe0e\ufe0f" else c),
        ("casefold", str.casefold),
        ("remove_separators", lambda c: "" if c.isspace() or c in "-_." else c),
    ):
        chars, mapped = [], []
        for char, span in zip(text, spans):
            part = operation(char)
            chars.extend(part)
            mapped.extend([span] * len(part))
        text, spans, steps = "".join(chars), mapped, steps + (name,)
        yield text, spans, steps


def _plain(text: str, canaries: list[str]) -> list[Finding]:
    found = {}
    needles = {c: list(_stages(c)) for c in canaries if c}
    for stage, (normalized, spans, steps) in enumerate(_stages(text)):
        for canary, variants in needles.items():
            needle = variants[stage][0]
            if not needle:
                continue
            start = 0
            while (index := normalized.find(needle, start)) >= 0:
                a, b = spans[index][0], spans[index + len(needle) - 1][1]
                found.setdefault((canary, a, b), Finding(canary, a, b, steps or ("exact",)))
                start = index + len(needle)
    return list(found.values())


def find_secrets(text: str, canaries: list[str]) -> list[Finding]:
    findings = _plain(text, canaries)
    normalized, positions, normalization = list(_stages(text))[2]
    if normalized == text:
        normalization = ()
    for kind, pattern in (("hex", r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{12,}(?![0-9A-Fa-f])"),
                          ("base64", r"(?<![A-Za-z0-9+/_-])[A-Za-z0-9+/_-]{12,}={0,2}(?![A-Za-z0-9+/_=-])")):
        for match in re.finditer(pattern, normalized):
            token = match.group()
            if len(token) > 16384:
                continue
            try:
                raw = (bytes.fromhex(token) if kind == "hex" else
                       base64.b64decode(token + "=" * (-len(token) % 4), altchars=b"-_", validate=True))
                decoded = raw.decode("utf-8")
            except (ValueError, UnicodeDecodeError, binascii.Error):
                continue
            for finding in _plain(decoded, canaries):
                findings.append(Finding(finding.canary, positions[match.start()][0], positions[match.end() - 1][1],
                                        normalization + (kind,) + finding.transformations))
    return sorted(set(findings), key=lambda f: (f.start, f.end, f.canary, f.transformations))
