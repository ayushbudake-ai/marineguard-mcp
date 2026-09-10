import { NavLink } from "react-router";
import {
  LayoutDashboard,
  ScanSearch,
  Map,
  ShieldCheck,
  BarChart3,
  FileText,
  Info,
} from "lucide-react";

const NAV_ITEMS = [
  {
    to: "/",
    label: "Analyze",
    icon: ScanSearch,
    end: true,
  },
  {
  to: "/dashboard",
  label: "Dashboard",
  icon: LayoutDashboard,
  },
  {
    to: "/map",
    label: "Detection Map",
    icon: Map,
  },
  {
    to: "/firewall",
    label: "Mission Firewall",
    icon: ShieldCheck,
  },
  {
    to: "/metrics",
    label: "Metrics",
    icon: BarChart3,
  },
  {
    to: "/reports",
    label: "Reports",
    icon: FileText,
  },
  {
    to: "/about",
    label: "About",
    icon: Info,
  },
];

export default function Sidebar() {
  return (
    <aside className="flex min-h-screen w-64 flex-col border-r border-line bg-surface">
      {/* Logo / Brand */}
      <div className="border-b border-line px-6 py-6">
        <div className="font-mono text-lg font-bold tracking-widest text-teal">
          MARINEGUARD
        </div>

        <p className="mt-1 text-xs text-muted">
          Marine debris detection console
        </p>
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
                group flex items-center gap-3 rounded-md px-4 py-3
                text-sm font-medium transition-all duration-200
                ${
                  isActive
                    ? "bg-teal/10 text-teal"
                    : "text-muted hover:bg-surface2 hover:text-fg"
                }
                `
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    size={18}
                    strokeWidth={isActive ? 2.2 : 1.8}
                    className="shrink-0"
                  />

                  <span>{item.label}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom Status */}
      <div className="border-t border-line px-5 py-5">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-amber" />

          <span className="text-xs text-muted">
            Mock data mode
          </span>
        </div>

        <p className="mt-2 text-[11px] leading-relaxed text-muted">
          No backend connected
        </p>
      </div>
    </aside>
  );
}