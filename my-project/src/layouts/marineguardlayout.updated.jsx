import { Outlet } from "react-router";
import Sidebar from "../components/sidebar";

export default function DashboardLayout() {
  return (
    <div className="flex min-h-screen bg-ink">
      <Sidebar />

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
