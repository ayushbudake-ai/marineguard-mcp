import { type RouteConfig, index, route, layout } from "@react-router/dev/routes";

export default [
  layout("../src/layouts/marineguardlayout.updated.jsx", [
    index("../src/pages/Analyze.jsx"),
    route("dashboard", "../src/pages/Dashboard.jsx"),
    route("evidence/:detectionId?", "../src/pages/EvidenceReview.jsx"),
    route("metrics", "../src/pages/Metrics.jsx"),
    route("reports", "../src/pages/Report.jsx"),
    route("about", "../src/pages/About.jsx"),
    route("firewall", "../src/pages/MissionFirewall.jsx"),
    route("mcp-tools", "../src/pages/McpToolServer.updated.jsx"),
  ]),
] satisfies RouteConfig;
