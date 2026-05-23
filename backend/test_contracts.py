"""Guard the one hand-synced cross-language contract: the A2UI component names.

`COMPONENT_NAMES` in backend/agents.py (what the model is told it may emit) MUST
equal the keys of `demonstrationCatalogDefinitions` in
frontend/src/catalog/definitions.ts (what the frontend catalog can render). They
live in different languages, never import each other, and are matched by string
equality at runtime — so drift is silent (model emits a component the catalog
can't draw). See README "Contracts".

Pure text parsing on purpose: importing backend.agents would construct the
Pydantic AI agents, which requires real API keys at import time. This test must
run without any keys, so it reads both files as text.

Runs standalone (`uv run python -m backend.test_contracts`) or under pytest.
"""

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_AGENTS_PY = _ROOT / "backend" / "agents.py"
_DEFINITIONS_TS = _ROOT / "frontend" / "src" / "catalog" / "definitions.ts"


def _backend_component_names() -> list[str]:
    """Extract the string literals inside the COMPONENT_NAMES = [...] list."""
    text = _AGENTS_PY.read_text()
    block = re.search(r"COMPONENT_NAMES\s*=\s*\[(.*?)\]", text, re.DOTALL)
    assert block, "COMPONENT_NAMES list not found in backend/agents.py"
    return re.findall(r'"([A-Za-z]+)"', block.group(1))


def _frontend_definition_keys() -> list[str]:
    """Extract top-level keys of demonstrationCatalogDefinitions (2-space indent)."""
    text = _DEFINITIONS_TS.read_text()
    block = re.search(
        r"demonstrationCatalogDefinitions\s*=\s*\{(.*)\n\};", text, re.DOTALL
    )
    assert block, "demonstrationCatalogDefinitions object not found in definitions.ts"
    return re.findall(r"^ {2}(\w+): \{", block.group(1), re.MULTILINE)


def test_component_names_match_catalog_definitions() -> None:
    backend = _backend_component_names()
    frontend = _frontend_definition_keys()
    assert set(backend) == set(frontend), (
        "A2UI component contract drift between backend prompt and frontend catalog.\n"
        f"  only in COMPONENT_NAMES (agents.py): {sorted(set(backend) - set(frontend))}\n"
        f"  only in definitions.ts:              {sorted(set(frontend) - set(backend))}"
    )


if __name__ == "__main__":
    test_component_names_match_catalog_definitions()
    print(f"OK — {len(_backend_component_names())} component names in sync")
