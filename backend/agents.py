import json

from pydantic_ai import Agent
from typing_extensions import TypedDict

from backend import a2ui

# Mirrors the notebook's two create_agent() calls — same system prompt, Pydantic AI style.
openai_agent = Agent("openai:gpt-4.1", system_prompt="You are a helpful assistant")
claude_agent = Agent("anthropic:claude-haiku-4-5", system_prompt="You are a helpful assistant")


# ── L4: A2UI (declarative generative UI) agent ───────────────────────────────
# Additive. The Node @ag-ui/a2ui-middleware (scoped to this agent in server.ts)
# injects the dynamic `render_a2ui` frontend tool and the A2UI protocol guidelines.

CATALOG_ID = "copilotkit://app-dashboard-catalog"
SURFACE_ID = "flight-search-results"

# Fixed flight-card carousel: a predefined, data-bound A2UI component tree
# (ported verbatim from the L4 notebook, originally produced by the A2UI Composer).
#
# This is *true* declarative data binding — the schema is fixed and only the data
# changes per call. The root List uses a structural-children template
# {componentId: "flight-card", path: "/flights"}: the renderer's GenericBinder
# scrapes the List schema (a Zod union containing {componentId, path}), classifies
# `children` as STRUCTURAL, subscribes to /flights in the data model, and expands
# one "flight-card" instance per array element. Each instance renders with a scoped
# basePath (/flights/0, /flights/1, ...), so child props like {"path": "airline"}
# resolve *relative* to that base (→ /flights/0/airline). display_flights therefore
# emits the schema once + an updateDataModel that seeds {"flights": [...]} at root.
#
# (Note: this works in a *custom* Zod catalog — the binder keys on schema shape, not
# on the basic catalog — provided zod is v3, which the renderer's scraper requires.)

FLIGHT_SCHEMA = [
    {"id": "root", "component": "List", "children": {"componentId": "flight-card", "path": "/flights"}, "direction": "horizontal", "gap": 16},
    {"id": "flight-card", "component": "Card", "child": "main-col"},
    {"id": "main-col", "component": "Column", "children": ["airline-img", "header-row", "meta-row", "divider-1", "times-row", "route-row", "divider-2", "status-row", "divider-3", "book-btn"], "align": "stretch", "gap": 8},
    {"id": "airline-img", "component": "Image", "src": {"path": "airlineLogo"}, "alt": {"path": "airline"}, "height": 32},
    {"id": "header-row", "component": "Row", "children": ["airline-name", "price-text"], "justify": "spaceBetween", "align": "center"},
    {"id": "airline-name", "component": "Text", "text": {"path": "airline"}, "variant": "h3"},
    {"id": "price-text", "component": "Text", "text": {"path": "price"}, "variant": "h2"},
    {"id": "meta-row", "component": "Row", "children": ["flight-number", "date-text"], "justify": "spaceBetween", "align": "center"},
    {"id": "flight-number", "component": "Text", "text": {"path": "flightNumber"}, "variant": "caption"},
    {"id": "date-text", "component": "Text", "text": {"path": "date"}, "variant": "caption"},
    {"id": "divider-1", "component": "Divider"},
    {"id": "times-row", "component": "Row", "children": ["depart-time", "duration-text", "arrive-time"], "justify": "spaceBetween", "align": "center"},
    {"id": "depart-time", "component": "Text", "text": {"path": "departureTime"}, "variant": "h2"},
    {"id": "duration-text", "component": "Text", "text": {"path": "duration"}, "variant": "caption"},
    {"id": "arrive-time", "component": "Text", "text": {"path": "arrivalTime"}, "variant": "h2"},
    {"id": "route-row", "component": "Row", "children": ["origin-code", "arrow-text", "dest-code"], "justify": "spaceBetween", "align": "center"},
    {"id": "origin-code", "component": "Text", "text": {"path": "origin"}, "variant": "h3"},
    {"id": "arrow-text", "component": "Text", "text": "→", "variant": "h3"},
    {"id": "dest-code", "component": "Text", "text": {"path": "destination"}, "variant": "h3"},
    {"id": "divider-2", "component": "Divider"},
    {"id": "status-row", "component": "Row", "children": ["status-text"], "align": "center"},
    {"id": "status-text", "component": "Text", "text": {"path": "status"}, "variant": "caption"},
    {"id": "divider-3", "component": "Divider"},
    {"id": "book-btn", "component": "Button", "label": "Book Flight", "variant": "primary", "action": {"event": {"name": "bookFlight"}}},
]


class Flight(TypedDict):
    id: str
    airline: str
    airlineLogo: str
    flightNumber: str
    origin: str
    destination: str
    date: str
    departureTime: str
    arrivalTime: str
    duration: str
    status: str
    price: str


a2ui_agent = Agent(
    "anthropic:claude-sonnet-4-6",
    system_prompt=(
        "You are a helpful assistant that creates rich visual UI.\n\n"
        "Tool guidance:\n"
        "- ALL flight-related queries: first call search_flights to fetch flight "
        "data, then call display_flights with the results. NEVER use render_a2ui "
        "for flights.\n"
        "- For sales/business data requests: first call get_sales_data to fetch "
        "the latest metrics, then call render_a2ui to visualize the results as a "
        "dashboard with charts, metrics, and cards.\n"
        "- For other rich UI: call render_a2ui directly.\n\n"
        "When you call render_a2ui you MUST:\n"
        f'- Pass catalogId exactly "{CATALOG_ID}". Never omit it and never use "basic".\n'
        "- Build the `components` array using ONLY these component names, each as a "
        "  `component` field (NOT `type`): Title, Text, Icon, Image, Divider, Card, "
        "  List, Tabs, Row, Column, DashboardCard, Metric, PieChart, BarChart, Badge, "
        "  DataTable, Button. There is no `Box` component.\n"
        "- Put each component's props as flat keys on the object (not nested under "
        "  `props`). Exactly one component has id \"root\".\n"
        "- Use inline literal values (e.g. Metric value \"$1.2M\"; PieChart/BarChart "
        "  data as an inline array of {label, value}). Do not use {path:...} bindings.\n"
        "Example components array for a dashboard:\n"
        '[{"id":"root","component":"Column","gap":16,"children":["t","m","c"]},'
        '{"id":"t","component":"Title","text":"Sales Dashboard","level":"h1"},'
        '{"id":"m","component":"Row","gap":16,"children":["m1"]},'
        '{"id":"m1","component":"DashboardCard","title":"Revenue","child":"m1v"},'
        '{"id":"m1v","component":"Metric","label":"Total Revenue","value":"$1.2M","trend":"up","trendValue":"4.7%"},'
        '{"id":"c","component":"DashboardCard","title":"Revenue by Category","child":"pie"},'
        '{"id":"pie","component":"PieChart","data":[{"label":"Electronics","value":420000},{"label":"Books","value":125000}]}]\n\n'
        "IMPORTANT: After calling a tool, do NOT repeat or summarize the data "
        "in your text response. The tool renders UI automatically. "
        "Just confirm what was rendered."
    ),
)


@a2ui_agent.tool_plain
def get_sales_data() -> str:
    """Fetch current sales metrics and revenue data.

    Returns sales data including revenue, customers, conversion rates,
    and breakdowns by category and month.
    """
    return json.dumps({
        "totalRevenue": "$1.2M",
        "newCustomers": 3842,
        "conversionRate": "3.6%",
        "revenueByCategory": [
            {"label": "Electronics", "value": 420000},
            {"label": "Clothing", "value": 310000},
            {"label": "Home & Garden", "value": 185000},
            {"label": "Sports", "value": 160000},
            {"label": "Books", "value": 125000},
        ],
        "monthlySales": [
            {"label": "Jan", "value": 85000},
            {"label": "Feb", "value": 92000},
            {"label": "Mar", "value": 108000},
            {"label": "Apr", "value": 95000},
            {"label": "May", "value": 115000},
            {"label": "Jun", "value": 125000},
        ],
    })


@a2ui_agent.tool_plain
def search_flights(origin: str, destination: str) -> list[Flight]:
    """Search for available flights between two airports.

    Args:
        origin: Origin airport IATA code (e.g. "SFO").
        destination: Destination airport IATA code (e.g. "JFK").
    """
    return [
        {"id": "1", "airline": "Delta Air Lines", "airlineLogo": "https://www.gstatic.com/flights/airline_logos/70px/DL.png", "flightNumber": "DL 520", "origin": origin, "destination": destination, "date": "2026-04-11", "departureTime": "08:00", "arrivalTime": "16:35", "duration": "5h 35m", "status": "On Time", "price": "$389"},
        {"id": "2", "airline": "United Airlines", "airlineLogo": "https://www.gstatic.com/flights/airline_logos/70px/UA.png", "flightNumber": "UA 1583", "origin": origin, "destination": destination, "date": "2026-04-11", "departureTime": "10:15", "arrivalTime": "18:42", "duration": "5h 27m", "status": "On Time", "price": "$412"},
        {"id": "3", "airline": "JetBlue", "airlineLogo": "https://www.gstatic.com/flights/airline_logos/70px/B6.png", "flightNumber": "B6 416", "origin": origin, "destination": destination, "date": "2026-04-11", "departureTime": "14:30", "arrivalTime": "23:05", "duration": "5h 35m", "status": "On Time", "price": "$345"},
        {"id": "4", "airline": "American Airlines", "airlineLogo": "https://www.gstatic.com/flights/airline_logos/70px/AA.png", "flightNumber": "AA 178", "origin": origin, "destination": destination, "date": "2026-04-11", "departureTime": "17:00", "arrivalTime": "01:20+1", "duration": "5h 20m", "status": "On Time", "price": "$398"},
    ]


@a2ui_agent.tool_plain
def display_flights(flights: list[Flight]) -> dict:
    """Display flights as rich cards in a horizontal row.

    Each flight must have: id, airline, airlineLogo (URL), flightNumber,
    origin, destination, date, departureTime, arrivalTime, duration,
    status, and price.
    """
    return a2ui.render([
        a2ui.create_surface(SURFACE_ID, CATALOG_ID),
        a2ui.update_components(SURFACE_ID, FLIGHT_SCHEMA),
        a2ui.update_data_model(SURFACE_ID, {"flights": flights}),
    ])
