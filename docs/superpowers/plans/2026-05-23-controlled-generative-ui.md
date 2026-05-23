# Controlled Generative UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Register FlightCard and PieChart as agent-callable UI components via `useComponent()`, and set Claude as the default agent.

**Architecture:** Two new self-contained component files (schema + component co-located), registered in App.tsx via `useComponent()`. No backend changes — the agent's existing tool-call support handles the rest.

**Tech Stack:** React 18, CopilotKit v2, Zod (schema), Recharts (pie chart), Tailwind (styling via CopilotKit's included CSS)

---

### Task 1: Install dependencies

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Install zod and recharts**

```bash
npm --prefix frontend add zod recharts
```

Expected output: added 2 packages (or similar), no errors.

- [ ] **Step 2: Verify installs**

```bash
cat frontend/package.json | grep -E '"zod"|"recharts"'
```

Expected: both appear under `dependencies`.

---

### Task 2: Create FlightCard component

**Files:**
- Create: `frontend/src/components/flight-card.tsx`

- [ ] **Step 1: Create the file**

```tsx
import { z } from "zod";

export const FlightCardProps = z.object({
  title: z.string().describe("Flight card title"),
  airline: z.string().describe("Airline name"),
  origin: z.string().describe("Departure airport code or city"),
  destination: z.string().describe("Arrival airport code or city"),
  departure_time: z.string().describe("Departure time"),
  price: z.string().describe("Price display string e.g. $249"),
});

type FlightCardPropsType = z.infer<typeof FlightCardProps>;

export function FlightCard({
  title,
  airline,
  origin,
  destination,
  departure_time,
  price,
}: FlightCardPropsType) {
  return (
    <div style={{ borderRadius: 8, border: "1px solid #e0e0e0", background: "#fff", padding: 12, marginTop: 8, maxWidth: 340 }}>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>{title}</div>
      <div style={{ border: "1px solid #e0e0e0", borderRadius: 6, padding: 10, fontSize: 14 }}>
        <div style={{ fontWeight: 500 }}>{airline}</div>
        <div>{origin} → {destination}</div>
        <div>Departs: {departure_time}</div>
        <div style={{ fontWeight: 600, marginTop: 4 }}>{price}</div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify file exists**

```bash
ls frontend/src/components/flight-card.tsx
```

Expected: file path printed with no error.

---

### Task 3: Create PieChart component

**Files:**
- Create: `frontend/src/components/pie-chart.tsx`

- [ ] **Step 1: Create the file**

```tsx
import { z } from "zod";
import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export const PieChartProps = z.object({
  title: z.string().describe("Chart title"),
  data: z
    .array(
      z.object({
        name: z.string().describe("Slice label"),
        value: z.number().describe("Numeric value"),
      })
    )
    .describe("Array of data points"),
});

type PieChartPropsType = z.infer<typeof PieChartProps>;

const COLORS = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe"];

export function PieChart({ title, data }: PieChartPropsType) {
  return (
    <div style={{ marginTop: 8, maxWidth: 400 }}>
      <div style={{ fontWeight: 600, marginBottom: 8 }}>{title}</div>
      <ResponsiveContainer width="100%" height={260}>
        <RechartsPieChart>
          <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **Step 2: Verify file exists**

```bash
ls frontend/src/components/pie-chart.tsx
```

Expected: file path printed with no error.

---

### Task 4: Update App.tsx

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Replace the entire file content**

```tsx
import { useState } from "react";
import { z } from "zod";
import { CopilotChat } from "@copilotkit/react-core/v2";
import { useComponent } from "@copilotkit/react-core/v2";
import { FlightCard, FlightCardProps } from "./components/flight-card";
import { PieChart, PieChartProps } from "./components/pie-chart";

type AgentId = "default" | "claude";

export default function App() {
  const [agentId, setAgentId] = useState<AgentId>("claude");

  useComponent({
    name: "flightCard",
    description: "Displays a flight summary card with airline, route, departure time, and price.",
    parameters: FlightCardProps,
    render: FlightCard,
  });

  useComponent({
    name: "pieChart",
    description: "Displays data as a pie chart. Use when the user asks for a chart, graph, or visual breakdown of data.",
    parameters: PieChartProps,
    render: PieChart,
  });

  return (
    <div style={{ height: "100%", position: "relative" }}>
      <select
        className="agent-switch"
        value={agentId}
        onChange={(e) => setAgentId(e.target.value as AgentId)}
      >
        <option value="claude">Claude (haiku-4-5)</option>
        <option value="default">OpenAI (gpt-4.1)</option>
      </select>
      <CopilotChat key={agentId} agentId={agentId} />
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
npm --prefix frontend run build 2>&1 | tail -20
```

Expected: `built in Xs` with no TypeScript errors. If errors appear, check import paths match exactly — no `@/` alias exists in this project.

---

### Task 5: Run the app

- [ ] **Step 1: Start all services**

```bash
npm run dev
```

Run from the repo root (`/Users/shubh/Desktop/src/copilotkit`). This starts backend (8002), runtime (4002), and frontend (3002) concurrently.

- [ ] **Step 2: Verify services are up**

Expected terminal output includes:
- `backend  | INFO:     Application startup complete.`
- `runtime  | Server listening on port 4002`
- `frontend | Local: http://localhost:3002/`

- [ ] **Step 3: Test FlightCard**

Open `http://localhost:3002` in browser. Send message:
> "Show a flight card for Pacific Air from SFO to JFK departing at 08:30 for $249"

Expected: a styled FlightCard renders in the chat response.

- [ ] **Step 4: Test PieChart**

Send message:
> "Show me a pie chart of revenue by category: Software 40%, Services 35%, Hardware 25%"

Expected: a Recharts PieChart renders in the chat response.

- [ ] **Step 5: Verify Claude is default**

On page load, the dropdown should show "Claude (haiku-4-5)" selected by default.
