# Controlled Generative UI — Design Spec
**Date:** 2026-05-23  
**Status:** Approved

## Overview

Add Controlled Generative UI to the existing CopilotKit app by registering two React components (`FlightCard`, `PieChart`) as agent-callable tools via `useComponent()`. Also set Claude as the default agent.

## Scope

- 2 new component files
- 2 package installs (`zod`, `recharts`)
- 2 modifications to existing files (`App.tsx`, `package.json`)
- No backend changes

## Architecture

The `useComponent()` hook exposes a React component to the agent as a tool. When the user asks something relevant, the agent calls the tool with structured JSON matching the Zod schema — the component renders that data in chat.

```
User prompt → Agent picks tool → Calls useComponent tool with args → React component renders in CopilotChat
```

## Files

### New: `frontend/src/components/flight-card.tsx`
- Zod schema `FlightCardProps`: `title`, `airline`, `origin`, `destination`, `departure_time`, `price` (all strings)
- `FlightCard` React component: renders a styled card using Tailwind classes
- Exports both schema and component

### New: `frontend/src/components/pie-chart.tsx`
- Zod schema `PieChartProps`: `title` (string), `data` (array of `{ name: string, value: number }`)
- `PieChart` React component: uses Recharts `PieChart` + `Pie` + `Tooltip` + `Legend`
- Exports both schema and component

### Modified: `frontend/src/App.tsx`
- Change default `agentId` state from `"default"` to `"claude"`
- Add `useComponent()` call for `flightCard`
- Add `useComponent()` call for `pieChart`
- Import both components and schemas

### Modified: `frontend/package.json`
- Add `zod` (schema validation, same library as backend Pydantic equivalent)
- Add `recharts` (pie chart rendering)

## Constraints

- Use `@copilotkit/react-core/v2` import path (already established in codebase)
- Tailwind CSS is available (already used via CopilotKit styles)
- `@/` path alias resolves to `frontend/src/` — verify in `vite.config.ts` before use, fall back to relative imports if not configured

## Success Criteria

1. App starts without errors (`npm run dev` from root)
2. Asking "show a flight card from SFO to JFK" renders a FlightCard in chat
3. Asking "show a pie chart of revenue by category" renders a PieChart in chat
4. Default agent on load is Claude (haiku-4-5), not OpenAI
