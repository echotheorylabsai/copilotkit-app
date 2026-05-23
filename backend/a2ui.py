"""Minimal A2UI envelope builder (no copilotkit/langgraph dependency).

Replicates the operation shapes the notebook's `copilotkit.a2ui` helper produces,
in the exact form expected by the Node `@ag-ui/a2ui-middleware`: a tool result whose
JSON carries an `a2ui_operations` array of per-operation objects.
"""

_V = "v0.9"  # protocol version; renderer ignores it (verified) but A2UI v0.9 docs require it


def create_surface(surface_id: str, catalog_id: str) -> dict:
    return {"version": _V, "createSurface": {"surfaceId": surface_id, "catalogId": catalog_id}}


def update_components(surface_id: str, components: list[dict]) -> dict:
    return {"version": _V, "updateComponents": {"surfaceId": surface_id, "components": components}}


def update_data_model(surface_id: str, value: dict, path: str = "/") -> dict:
    return {"version": _V, "updateDataModel": {"surfaceId": surface_id, "path": path, "value": value}}


def render(operations: list[dict]) -> dict:
    # Key `a2ui_operations` is what @ag-ui/a2ui-middleware detects in the tool result.
    return {"a2ui_operations": operations}
