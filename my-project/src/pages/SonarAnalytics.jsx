import {
  Activity,
  AlertTriangle,
  BarChart3,
  Radio,
  Target,
  Waves,
} from "lucide-react";

import SonarVisualizer from "../components/Sonarvisualizer";
import {
  getDetectionStats,
  getMockDetections,
} from "./mockdetection";

export default function SonarAnalytics() {
  const detections = getMockDetections();
  const stats = getDetectionStats();

  const averageDepth =
    detections.length > 0
      ? Math.round(
          detections.reduce(
            (sum, detection) => sum + detection.depth,
            0
          ) / detections.length
        )
      : 0;

  const highConfidence = detections.filter(
    (detection) => detection.confidence >= 90
  ).length;

  const averageConfidence =
    detections.length > 0
      ? Math.round(
          detections.reduce(
            (sum, detection) => sum + detection.confidence,
            0
          ) / detections.length
        )
      : 0;

  return (
    <div className="space-y-6">
      {/* --------------------------------------------- */}
      {/* PAGE HEADER */}
      {/* --------------------------------------------- */}

      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <div className="flex items-center gap-3">
            <div className="rounded-md bg-teal/10 p-2">
              <BarChart3
                size={20}
                className="text-teal"
              />
            </div>

            <div>
              <h1 className="font-mono text-xl font-semibold tracking-wide text-fg">
                SONAR ANALYTICS
              </h1>

              <p className="mt-1 text-sm text-muted">
                Acoustic sensor analysis and detection statistics
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-md border border-line bg-surface px-4 py-2">
          <span className="h-2 w-2 animate-pulse rounded-full bg-teal" />

          <span className="font-mono text-xs text-teal">
            SONAR-AUV-01 ACTIVE
          </span>
        </div>
      </div>

      {/* --------------------------------------------- */}
      {/* STATISTICS */}
      {/* --------------------------------------------- */}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <AnalyticsCard
          icon={Target}
          label="TOTAL DETECTIONS"
          value={stats.total}
          description="Objects detected"
        />

        <AnalyticsCard
          icon={Activity}
          label="AVG CONFIDENCE"
          value={`${averageConfidence}%`}
          description="Detection confidence"
        />

        <AnalyticsCard
          icon={Waves}
          label="AVG DEPTH"
          value={`${averageDepth}m`}
          description="Average detection depth"
        />

        <AnalyticsCard
          icon={AlertTriangle}
          label="HIGH CONFIDENCE"
          value={highConfidence}
          description="Confidence above 90%"
        />
      </div>

      {/* --------------------------------------------- */}
      {/* SONAR VISUALIZER */}
      {/* --------------------------------------------- */}

      <SonarVisualizer
        detections={detections.map(
          (detection, index) => ({
            id: detection.id,
            label: detection.type,
            confidence: detection.confidence,

            x:
              [28, 67, 55, 78, 38, 62][index] ??
              50,

            y:
              [35, 27, 68, 72, 48, 58][index] ??
              50,

            size:
              detection.risk === "High"
                ? 13
                : detection.risk === "Medium"
                  ? 10
                  : 8,
          })
        )}
      />

      {/* --------------------------------------------- */}
      {/* ANALYTICS GRID */}
      {/* --------------------------------------------- */}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ConfidenceAnalysis
          detections={detections}
        />

        <DepthAnalysis
          detections={detections}
        />
      </div>

      {/* --------------------------------------------- */}
      {/* SENSOR STATUS */}
      {/* --------------------------------------------- */}

      <SensorStatus />
    </div>
  );
}

/* ================================================== */
/* ANALYTICS CARD */
/* ================================================== */

function AnalyticsCard({
  icon: Icon,
  label,
  value,
  description,
}) {
  return (
    <div className="rounded-lg border border-line bg-surface p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-mono text-[10px] tracking-widest text-muted">
            {label}
          </p>

          <p className="mt-3 font-mono text-2xl font-semibold text-fg">
            {value}
          </p>
        </div>

        <div className="rounded-md bg-teal/10 p-2">
          <Icon
            size={18}
            className="text-teal"
          />
        </div>
      </div>

      <p className="mt-3 text-xs text-muted">
        {description}
      </p>
    </div>
  );
}

/* ================================================== */
/* CONFIDENCE ANALYSIS */
/* ================================================== */

function ConfidenceAnalysis({ detections }) {
  return (
    <section className="rounded-lg border border-line bg-surface">
      <div className="border-b border-line px-5 py-4">
        <div className="flex items-center gap-2">
          <Activity
            size={16}
            className="text-teal"
          />

          <h2 className="font-mono text-sm font-semibold tracking-wide text-fg">
            CONFIDENCE ANALYSIS
          </h2>
        </div>

        <p className="mt-1 text-xs text-muted">
          Detection confidence by object
        </p>
      </div>

      <div className="space-y-5 p-5">
        {detections.map((detection) => (
          <div key={detection.id}>
            <div className="mb-2 flex items-center justify-between">
              <div>
                <span className="font-mono text-xs text-teal">
                  {detection.id}
                </span>

                <span className="ml-3 text-xs text-fg">
                  {detection.type}
                </span>
              </div>

              <span className="font-mono text-xs text-fg">
                {detection.confidence}%
              </span>
            </div>

            <div className="h-2 overflow-hidden rounded-full bg-surface2">
              <div
                className="h-full rounded-full bg-teal transition-all duration-500"
                style={{
                  width: `${detection.confidence}%`,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ================================================== */
/* DEPTH ANALYSIS */
/* ================================================== */

function DepthAnalysis({ detections }) {
  const maxDepth = Math.max(
    ...detections.map(
      (detection) => detection.depth
    )
  );

  return (
    <section className="rounded-lg border border-line bg-surface">
      <div className="border-b border-line px-5 py-4">
        <div className="flex items-center gap-2">
          <Waves
            size={16}
            className="text-teal"
          />

          <h2 className="font-mono text-sm font-semibold tracking-wide text-fg">
            DEPTH ANALYSIS
          </h2>
        </div>

        <p className="mt-1 text-xs text-muted">
          Detection distribution by depth
        </p>
      </div>

      <div className="space-y-5 p-5">
        {detections.map((detection) => {
          const percentage =
            maxDepth > 0
              ? (detection.depth / maxDepth) * 100
              : 0;

          return (
            <div key={detection.id}>
              <div className="mb-2 flex items-center justify-between">
                <div>
                  <span className="font-mono text-xs text-teal">
                    {detection.id}
                  </span>

                  <span className="ml-3 text-xs text-fg">
                    {detection.type}
                  </span>
                </div>

                <span className="font-mono text-xs text-muted">
                  {detection.depth}m
                </span>
              </div>

              <div className="h-2 overflow-hidden rounded-full bg-surface2">
                <div
                  className="h-full rounded-full bg-amber transition-all duration-500"
                  style={{
                    width: `${percentage}%`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

/* ================================================== */
/* SENSOR STATUS */
/* ================================================== */

function SensorStatus() {
  const sensors = [
    {
      name: "Primary Sonar",
      id: "SONAR-AUV-01",
      status: "Operational",
      signal: "98.4%",
    },
    {
      name: "Acoustic Receiver",
      id: "ACR-02",
      status: "Operational",
      signal: "97.8%",
    },
    {
      name: "Depth Sensor",
      id: "DEP-01",
      status: "Operational",
      signal: "99.2%",
    },
    {
      name: "Optical Sensor",
      id: "CAM-01",
      status: "Operational",
      signal: "96.8%",
    },
  ];

  return (
    <section className="rounded-lg border border-line bg-surface">
      <div className="border-b border-line px-5 py-4">
        <div className="flex items-center gap-2">
          <Radio
            size={16}
            className="text-teal"
          />

          <h2 className="font-mono text-sm font-semibold tracking-wide text-fg">
            SENSOR STATUS
          </h2>
        </div>

        <p className="mt-1 text-xs text-muted">
          MarineGuard sensor network
        </p>
      </div>

      <div className="grid grid-cols-1 divide-y divide-line md:grid-cols-2 md:divide-x md:divide-y-0">
        {sensors.map((sensor) => (
          <div
            key={sensor.id}
            className="flex items-center justify-between px-5 py-4"
          >
            <div className="flex items-center gap-3">
              <span className="h-2 w-2 rounded-full bg-teal" />

              <div>
                <p className="text-sm text-fg">
                  {sensor.name}
                </p>

                <p className="mt-1 font-mono text-[10px] text-muted">
                  {sensor.id}
                </p>
              </div>
            </div>

            <div className="text-right">
              <p className="font-mono text-xs text-teal">
                {sensor.signal}
              </p>

              <p className="mt-1 text-[10px] text-muted">
                {sensor.status}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}