import { useEffect, useState } from "react";
import { Radio, Crosshair } from "lucide-react";

const DEFAULT_DETECTIONS = [
  {
    id: 1,
    x: 28,
    y: 35,
    size: 10,
    label: "Debris",
    confidence: 94,
  },
  {
    id: 2,
    x: 67,
    y: 27,
    size: 8,
    label: "Object",
    confidence: 87,
  },
  {
    id: 3,
    x: 55,
    y: 68,
    size: 13,
    label: "Debris",
    confidence: 91,
  },
  {
    id: 4,
    x: 78,
    y: 72,
    size: 7,
    label: "Object",
    confidence: 82,
  },
];

export default function SonarVisualizer({
  detections = DEFAULT_DETECTIONS,
  title = "SONAR VISUALIZER",
}) {
  const [scanAngle, setScanAngle] = useState(0);
  const [activeDetection, setActiveDetection] = useState(null);

  // Animate sonar scanning line
  useEffect(() => {
    const interval = setInterval(() => {
      setScanAngle((angle) => (angle + 2) % 360);
    }, 40);

    return () => clearInterval(interval);
  }, []);

  return (
    <section className="w-full overflow-hidden rounded-lg border border-line bg-surface">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-line px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-teal/10">
            <Radio size={18} className="text-teal" />
          </div>

          <div>
            <h2 className="font-mono text-sm font-semibold tracking-wider text-fg">
              {title}
            </h2>

            <p className="mt-1 text-xs text-muted">
              Real-time acoustic detection view
            </p>
          </div>
        </div>

        {/* Live indicator */}
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 animate-pulse rounded-full bg-teal" />

          <span className="font-mono text-[11px] tracking-wide text-teal">
            SCANNING
          </span>
        </div>
      </div>

      {/* Sonar Area */}
      <div className="p-5">
        <div
          className="relative aspect-video overflow-hidden rounded-md border border-line bg-[#061214]"
          onMouseLeave={() => setActiveDetection(null)}
        >
          {/* Grid */}
          <div className="pointer-events-none absolute inset-0">
            {/* Vertical lines */}
            <div className="absolute inset-y-0 left-1/4 border-l border-teal/10" />
            <div className="absolute inset-y-0 left-1/2 border-l border-teal/10" />
            <div className="absolute inset-y-0 left-3/4 border-l border-teal/10" />

            {/* Horizontal lines */}
            <div className="absolute inset-x-0 top-1/4 border-t border-teal/10" />
            <div className="absolute inset-x-0 top-1/2 border-t border-teal/10" />
            <div className="absolute inset-x-0 top-3/4 border-t border-teal/10" />
          </div>

          {/* Center sonar */}
          <div className="absolute left-1/2 top-1/2 h-[75%] aspect-square -translate-x-1/2 -translate-y-1/2">
            {/* Outer circle */}
            <div className="absolute inset-0 rounded-full border border-teal/20" />

            {/* Second circle */}
            <div className="absolute inset-[16%] rounded-full border border-teal/20" />

            {/* Third circle */}
            <div className="absolute inset-[32%] rounded-full border border-teal/20" />

            {/* Fourth circle */}
            <div className="absolute inset-[48%] rounded-full border border-teal/20" />

            {/* Crosshair */}
            <div className="absolute left-1/2 top-0 h-full border-l border-teal/15" />

            <div className="absolute left-0 top-1/2 w-full border-t border-teal/15" />

            {/* Sonar sweep */}
            <div
              className="absolute left-1/2 top-1/2 h-1/2 w-[1px] origin-bottom bg-teal"
              style={{
                transform: `translateX(-50%) rotate(${scanAngle}deg)`,
                boxShadow: "0 0 12px rgba(45, 212, 191, 0.8)",
              }}
            />

            {/* Sweep glow */}
            <div
              className="absolute left-1/2 top-1/2 h-1/2 w-1/3 origin-bottom"
              style={{
                transform: `translateX(-50%) rotate(${scanAngle - 12}deg)`,
                background:
                  "linear-gradient(to top, rgba(45,212,191,0.15), transparent)",
                clipPath: "polygon(50% 100%, 100% 0, 0 0)",
              }}
            />

            {/* Center point */}
            <div className="absolute left-1/2 top-1/2 h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-teal shadow-[0_0_10px_rgba(45,212,191,0.8)]" />
          </div>

          {/* Detection points */}
          {detections.map((detection) => (
            <button
              key={detection.id}
              type="button"
              className="absolute -translate-x-1/2 -translate-y-1/2"
              style={{
                left: `${detection.x}%`,
                top: `${detection.y}%`,
              }}
              onMouseEnter={() => setActiveDetection(detection)}
              onFocus={() => setActiveDetection(detection)}
              onClick={() => setActiveDetection(detection)}
              aria-label={`Detection ${detection.id}`}
            >
              {/* Pulse */}
              <span
                className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 animate-ping rounded-full bg-amber/30"
                style={{
                  width: detection.size * 3,
                  height: detection.size * 3,
                }}
              />

              {/* Detection point */}
              <span
                className="relative block rounded-full border border-amber bg-amber/60"
                style={{
                  width: detection.size,
                  height: detection.size,
                  boxShadow: "0 0 12px rgba(251,191,36,0.7)",
                }}
              />
            </button>
          ))}

          {/* Detection information */}
          {activeDetection && (
            <div
              className="absolute z-20 rounded-md border border-line bg-surface/95 px-3 py-2 shadow-xl backdrop-blur"
              style={{
                left: `${Math.min(activeDetection.x + 3, 78)}%`,
                top: `${Math.min(activeDetection.y + 3, 78)}%`,
              }}
            >
              <div className="flex items-center gap-2">
                <Crosshair size={14} className="text-amber" />

                <span className="font-mono text-xs text-fg">
                  {activeDetection.label}
                </span>
              </div>

              <div className="mt-1 font-mono text-[10px] text-muted">
                ID #{String(activeDetection.id).padStart(3, "0")}
              </div>

              <div className="mt-1 font-mono text-xs text-teal">
                Confidence: {activeDetection.confidence}%
              </div>
            </div>
          )}

          {/* Coordinates */}
          <div className="absolute left-3 top-3 font-mono text-[10px] text-muted">
            00°00'00"N
          </div>

          <div className="absolute right-3 top-3 font-mono text-[10px] text-muted">
            DEPTH: 42m
          </div>

          <div className="absolute bottom-3 left-3 font-mono text-[10px] text-muted">
            SONAR-AUV-01
          </div>

          <div className="absolute bottom-3 right-3 font-mono text-[10px] text-muted">
            RANGE: 100m
          </div>
        </div>

        {/* Bottom information */}
        <div className="mt-4 grid grid-cols-3 gap-3">
          <InfoBox label="SCAN STATUS" value="ACTIVE" active />

          <InfoBox
            label="DETECTIONS"
            value={String(detections.length).padStart(2, "0")}
          />

          <InfoBox label="SIGNAL" value="98.4%" />
        </div>

        {/* Legend */}
        <div className="mt-4 flex flex-wrap items-center gap-5 border-t border-line pt-4">
          <LegendItem
            className="bg-amber"
            label="Detected object"
          />

          <LegendItem
            className="bg-teal"
            label="Sonar sweep"
          />

          <LegendItem
            className="border border-teal/30 bg-transparent"
            label="Range"
          />
        </div>
      </div>
    </section>
  );
}

function InfoBox({ label, value, active = false }) {
  return (
    <div className="rounded-md border border-line bg-surface2 px-4 py-3">
      <p className="font-mono text-[10px] tracking-wider text-muted">
        {label}
      </p>

      <p
        className={`mt-1 font-mono text-sm ${
          active ? "text-teal" : "text-fg"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function LegendItem({ className, label }) {
  return (
    <div className="flex items-center gap-2">
      <span className={`h-2.5 w-2.5 rounded-full ${className}`} />

      <span className="text-xs text-muted">
        {label}
      </span>
    </div>
  );
}