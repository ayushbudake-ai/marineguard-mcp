import {
  Bell,
  CircleHelp,
  Radio,
  User,
} from "lucide-react";

export default function Topbar() {
  return (
    <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-line bg-surface/95 px-6 backdrop-blur">
      {/* Left side */}
      <div className="flex items-center gap-4">
        <div>
          <p className="font-mono text-xs tracking-wider text-muted">
            SIH26057
          </p>

          <p className="text-sm font-medium text-fg">
            Ministry of Earth Sciences
          </p>
        </div>
      </div>

      {/* Center status */}
      <div className="hidden items-center gap-2 rounded-md border border-line bg-surface2 px-4 py-2 md:flex">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-teal opacity-50" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-teal" />
        </span>

        <Radio size={14} className="text-teal" />

        <span className="font-mono text-[11px] tracking-wide text-teal">
          AUV-01 ONLINE
        </span>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-2">
        {/* Help */}
        <button
          type="button"
          className="rounded-md p-2 text-muted transition-colors hover:bg-surface2 hover:text-fg"
          title="Help"
        >
          <CircleHelp size={18} />
        </button>

        {/* Notifications */}
        <button
          type="button"
          className="relative rounded-md p-2 text-muted transition-colors hover:bg-surface2 hover:text-fg"
          title="Notifications"
        >
          <Bell size={18} />

          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-amber" />
        </button>

        {/* User */}
        <div className="ml-2 flex items-center gap-3 border-l border-line pl-4">
          <div className="hidden text-right sm:block">
            <p className="text-xs font-medium text-fg">
              MarineGuard
            </p>

            <p className="font-mono text-[10px] text-muted">
              OPERATOR
            </p>
          </div>

          <div className="flex h-9 w-9 items-center justify-center rounded-full border border-line bg-surface2">
            <User size={17} className="text-teal" />
          </div>
        </div>
      </div>
    </header>
  );
}