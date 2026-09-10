// Drop this in as app/routes.ts (replacing the scaffold's default content).
// Adjust the "../src/..." paths if your pages end up living somewhere else.
//
// This assumes the scaffold's default app/ + src/ layout, i.e. src/ sits
// next to app/ at the project root. If TypeScript complains about .jsx
// imports here, add `"allowJs": true` to tsconfig.json — Vite itself will
// still serve the dev server fine either way, that's only a type-check
// nicety.

import { type RouteConfig, index, route, layout } from "@react-router/dev/routes";

export default [
  layout("../src/layouts/marineguardlayout.updated.jsx", [
    index("../src/pages/analyze.jsx"),
    route("dashboard", "../src/pages/dashboard.jsx"),
    route("map", "../src/layouts/detectionmap.jsx"),
    route("firewall", "../src/pages/MissionFirewall.jsx"),
    route("mcp-tools", "../src/pages/McpToolServer.updated.jsx"),
    route("evidence/:detectionId", "../src/pages/EvidenceReview.jsx"),
    route("metrics", "../src/pages/metrics.jsx"),
    route("reports", "../src/pages/report.jsx"),
    route("about", "../src/pages/about.jsx"),
  ]),
] satisfies RouteConfig;
