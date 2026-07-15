"""Model adapters.

Every model under test implements one method: complete(system, prompt) -> str.

- AnthropicAdapter: calls the Claude API (requires ANTHROPIC_API_KEY).
- MockAdapter: deterministic offline stand-in with configurable failure modes,
  so the whole suite (and CI) runs without network access or keys. The mock's
  injected failures are also how the validators themselves are tested — a
  validation framework you can't validate is just vibes.
"""
from __future__ import annotations

import hashlib
import os
import re
from typing import Protocol


class ModelAdapter(Protocol):
    name: str
    def complete(self, system: str, prompt: str) -> str: ...


class AnthropicAdapter:
    """Claude via the Anthropic API. pip install anthropic; set ANTHROPIC_API_KEY."""

    def __init__(self, model: str = "claude-sonnet-5"):
        import anthropic  # deferred so offline users never need it
        self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self.model = model
        self.name = f"anthropic:{model}"

    def complete(self, system: str, prompt: str) -> str:
        msg = self._client.messages.create(
            model=self.model, max_tokens=1024, system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text


class MockAdapter:
    """Deterministic offline model with seeded failure modes.

    failure_rate controls how often the mock deliberately violates policy
    (echoes a value it was told to redact). Failures are deterministic per
    prompt (hash-based), so runs are reproducible and defects are stable.
    """

    def __init__(self, name: str = "mock:baseline", failure_rate: float = 0.15):
        self.name = name
        self.failure_rate = failure_rate

    def _should_fail(self, prompt: str) -> bool:
        h = int(hashlib.sha256(prompt.encode()).hexdigest(), 16)
        return (h % 1000) / 1000 < self.failure_rate

    def complete(self, system: str, prompt: str) -> str:
        # Extract the document's field lines: "name (LABEL): value"
        fields = re.findall(r"^(\w+) \((\w+)\): (.+)$", prompt, re.M)
        fail = self._should_fail(prompt)
        out = ["Summary of the provided record:"]
        for name, label, value in fields:
            if label in ("CONFIDENTIAL", "RESTRICTED") and not fail:
                out.append(f"- {name}: [REDACTED:{label}]")
            elif label in ("CONFIDENTIAL", "RESTRICTED") and fail:
                out.append(f"- {name}: {value}")  # deliberate policy violation
                fail = False  # leak at most one field per response
            else:
                out.append(f"- {name}: {value}")
        return "\n".join(out)
