import { computeGeometry } from "../utils/mockGeometry";

export default function SensorCard({ sensor }) {
  const { altitudeM, rangeM, swathM } = computeGeometry(sensor.name);

  return (
    <div className="border border-line bg-surface px-4 py-4">
      <div className="text-sm text-fg">{sensor.name}</div>
      <div className="mt-0.5 text-xs text-muted">{sensor.detail}</div>

      <div className="mt-3 grid grid-cols-3 gap-2 border-t border-line pt-3">
        <Geo label="Altitude" value={altitudeM} unit="m" />
        <Geo label="Range" value={rangeM} unit="m" />
        <Geo label="Swath" value={swathM} unit="m" />
      </div>
      <div className="mt-2 font-mono text-[10px] uppercase tracking-wide text-amber">
        Example geometry — illustrative only
      </div>
    </div>
  );
}

function Geo({ label, value, unit }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wide text-muted">{label}</div>
      <div className="font-mono text-sm text-fg">
        {value}
        <span className="ml-0.5 text-xs text-muted">{unit}</span>
      </div>
    </div>
  );
}
