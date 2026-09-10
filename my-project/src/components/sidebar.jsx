import React, { useState, useEffect } from "react";
import { NavLink } from "react-router";
import {
  LayoutDashboard,
  ScanSearch,
  ShieldCheck,
  BarChart3,
  FileText,
  Info,
  Cpu,
  X,
  Layers,
  Sparkles,
} from "lucide-react";
import { checkHealth } from "../pages/marineguard";

const NAV_ITEMS = [
  {
    to: "/dashboard",
    label: "Dashboard",
    icon: LayoutDashboard,
  },
  {
    to: "/",
    label: "SSS Analysis",
    icon: ScanSearch,
    end: true,
  },
  {
    to: "/evidence",
    label: "Evidence",
    icon: ShieldCheck,
  },
  {
    to: "/metrics",
    label: "Metrics",
    icon: BarChart3,
  },
  {
    to: "/reports",
    label: "Exports",
    icon: FileText,
  },
  {
    to: "/about",
    label: "About",
    icon: Info,
  },
];

export default function Sidebar() {
  const [health, setHealth] = useState({ status: "checking", service: "MarineGuard MCP" });
  const [infoOpen, setInfoOpen] = useState(false);

  useEffect(() => {
    checkHealth().then(setHealth);
    const interval = setInterval(() => {
      checkHealth().then(setHealth);
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const isConnected = health.status === "ok";

  return (
    <>
      <aside className="flex min-h-screen w-64 flex-col border-r border-line bg-surface/90 backdrop-blur z-20">
        {/* Logo / Brand */}
        <div className="border-b border-line px-6 py-6">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm bg-teal shadow-lg shadow-teal/50" />
            <span className="font-mono text-lg font-bold tracking-widest text-fg">
              MARINEGUARD
            </span>
          </div>
          <p className="mt-1 text-[11px] text-muted font-mono uppercase tracking-wider">
            Side-Scan Sonar Console
          </p>

          {/* Model Status Card */}
          <button
            onClick={() => setInfoOpen(true)}
            className="mt-4 w-full text-left rounded-lg border border-teal/40 bg-teal/10 p-2.5 hover:bg-teal/20 transition-all group"
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs font-bold text-teal flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-teal animate-pulse" />
                SSS MODEL
              </span>
              <span className="text-[10px] font-mono text-teal/80 group-hover:underline">Info →</span>
            </div>
            <div className="mt-1 text-[10px] text-muted truncate">
              Unified SSS Detection Engine
            </div>
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex flex-1 flex-col gap-1 px-3 py-5">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `
                  group flex items-center gap-3 rounded-lg px-4 py-3
                  text-sm font-medium transition-all duration-200
                  ${
                    isActive
                      ? "bg-teal/15 text-teal border border-teal/30 shadow-sm"
                      : "text-muted hover:bg-surface2 hover:text-fg border border-transparent"
                  }
                  `
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      size={18}
                      strokeWidth={isActive ? 2.2 : 1.8}
                      className="shrink-0 text-current"
                    />
                    <span>{item.label}</span>
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Bottom Status */}
        <div className="border-t border-line px-5 py-4 bg-surface2/30">
          <div className="flex items-center gap-2">
            <span
              className={`h-2 w-2 rounded-full ${
                isConnected ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
              }`}
            />
            <span className="font-mono text-xs text-fg font-medium">
              {isConnected ? "BACKEND ONLINE" : "BACKEND OFFLINE"}
            </span>
          </div>

          <p className="mt-1 text-[10px] text-muted font-mono">
            FastAPI Bridge :8000
          </p>
        </div>
      </aside>

      {/* Model Information Modal / Drawer */}
      {infoOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-line bg-surface p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-start justify-between border-b border-line pb-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-teal/10 p-2 text-teal border border-teal/30">
                  <Cpu size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-fg">SSS MODEL Specification</h3>
                  <p className="text-xs text-muted">Unified Side-Scan Sonar Detection Engine</p>
                </div>
              </div>
              <button
                onClick={() => setInfoOpen(false)}
                className="rounded p-1 text-muted hover:bg-surface2 hover:text-fg"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between py-1 border-b border-line/50">
                <span className="text-muted">Product Model Name:</span>
                <span className="text-teal font-bold">SSS MODEL</span>
              </div>
              <div className="flex justify-between py-1 border-b border-line/50">
                <span className="text-muted">Architecture:</span>
                <span className="text-fg">YOLOv8n Object Detector</span>
              </div>
              <div className="flex justify-between py-1 border-b border-line/50">
                <span className="text-muted">Input Modality:</span>
                <span className="text-fg">Side-Scan Sonar (Acoustic Waterfall)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-line/50">
                <span className="text-muted">Supported SSS Classes:</span>
                <span className="text-teal font-bold">Ghost Net (net)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-line/50">
                <span className="text-muted">Role 3 Post-Processing:</span>
                <span className="text-fg">DetectionFilter (Confidence + Geometry)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-line/50">
                <span className="text-muted">Geolocation Policy:</span>
                <span className="text-fg">Recorded SSS metadata only</span>
              </div>
            </div>

            <div className="rounded-lg bg-surface2/60 border border-line p-3 text-xs leading-relaxed space-y-1 font-sans text-muted">
              <p className="font-semibold text-fg font-mono text-[11px] uppercase">
                Data Transparency Disclosure:
              </p>
              <p>
                Requested debris classes (Bottle, Can, Plastic, Tire, Other Debris) are monitored in our taxonomy but remain <b>NOT SUPPORTED BY CURRENT SSS DATA</b> due to lack of genuine Side-Scan Sonar training samples. We strictly enforce that optical underwater models are never masqueraded as sonar detectors.
              </p>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setInfoOpen(false)}
                className="px-4 py-2 text-xs font-medium rounded-lg bg-teal text-ink font-semibold hover:bg-teal/90 transition-colors"
              >
                Close Specification
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}