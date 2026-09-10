import { NavLink, Outlet } from "react-router";

const NAV_ITEMS = [
  { to: "/", label: "Analyze", end: true },
  { to: "/map", label: "Detection Map" },
  { to: "/firewall", label: "Mission Firewall" },
  { to: "/metrics", label: "Metrics" },
  { to: "/reports", label: "Reports" },
  { to: "/about", label: "About" },
];

export default function DashboardLayout() {
  return (
    <div className="flex min-h-screen bg-ink">
      <aside className="flex w-56 flex-col border-r border-line bg-surface">
        <div className="border-b border-line px-5 py-5">
          <div className="font-mono text-sm tracking-wide text-teal">MARINEGUARD</div>
          <div className="mt-1 text-xs text-muted">Debris detection console</div>
        </div>
        <nav className="flex flex-col gap-1 px-3 py-4">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `px-3 py-2 text-sm transition-colors ${
                  isActive ? "bg-teal/10 text-teal" : "text-muted hover:bg-surface2 hover:text-fg"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto border-t border-line px-5 py-4 text-xs text-muted">
          <span className="mr-2 inline-block h-2 w-2 rounded-full bg-amber align-middle" />
          Mock data mode — no backend connected
        </div>
      </aside>

      <div className="flex-1">
        <header className="flex items-center justify-between border-b border-line px-8 py-4">
          <div className="text-sm text-muted">SIH26057 — Ministry of Earth Sciences</div>
          <div className="font-mono text-xs text-muted">Sagar Netra (AUV-01)</div>
        </header>
        <main className="px-8 py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}