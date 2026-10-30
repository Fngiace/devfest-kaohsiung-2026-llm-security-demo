from common.llm import _client
from common.local_api import request
import pytest


def test_environment_cannot_redirect_inference(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "https://example.invalid")
    monkeypatch.setenv("HTTP_PROXY", "http://example.invalid:8080")
    client = _client()
    assert str(client._client.base_url) == "http://localhost:11434"
    assert client._client._trust_env is False
    client._client.close()


def test_direct_api_rejects_external_or_unlisted_paths():
    for path in ("https://example.invalid/api/chat", "//example.invalid", "/api/pull"):
        with pytest.raises(ValueError):
            request(path)
