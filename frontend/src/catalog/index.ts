// Assembles the A2UI catalog from its two halves: the schema `definitions`
// (what the agent may emit) and the React `renderers` (how each is drawn).
import { createCatalog } from "@copilotkit/a2ui-renderer";
import { demonstrationCatalogDefinitions } from "./definitions";
import { demonstrationCatalogRenderers } from "./renderers";

// Must match the backend exactly (backend/agents.py CATALOG_ID) and the catalogId
// the a2ui agent passes to render_a2ui. See README "Contracts".
export const CATALOG_ID = "copilotkit://app-dashboard-catalog";

export const demonstrationCatalog = createCatalog(
  demonstrationCatalogDefinitions,
  demonstrationCatalogRenderers,
  {
    catalogId: CATALOG_ID,
    includeBasicCatalog: false,
  },
);
