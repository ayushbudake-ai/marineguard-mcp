const STYLES = {
  LOW: "border-teal/50 bg-teal/10 text-teal",
  MEDIUM: "border-amber/50 bg-amber/10 text-amber",
  HIGH: "border-coral/50 bg-coral/10 text-coral",
  CRITICAL: "border-coral bg-coral/20 text-coral animate-firewall-pulse",
};

export default function RiskBadge({ level, size = "md" }) {
  const sizeClass = size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs";
  return (
    <span className={`inline-block border font-mono uppercase tracking-wide ${sizeClass} ${STYLES[level]}`}>
      {level}
    </span>
  );
}
