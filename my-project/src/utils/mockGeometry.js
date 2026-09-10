// Standin for geometry_solver.py, which computes real swath geometry,
// range, and altitude from sensor physics. That file's actual formulas
// weren't available to this session, so these numbers are illustrative
// placeholders only — deterministic per sensor name so they don't
// reshuffle on every render, but not a real physics computation.

function hashSeed(str) {
  let h = 2166136261 ^ str.length;
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 16777619);
  }
  return () => {
    h = Math.imul(h ^ (h >>> 15), 2246822519);
    h ^= h >>> 13;
    return ((h >>> 0) % 1000) / 1000;
  };
}

export function computeGeometry(sensorName) {
  const rand = hashSeed(sensorName);
  const altitudeM = Math.round(20 + rand() * 30);
  const rangeM = Math.round(75 + rand() * 100);
  const swathM = Math.round(rangeM * 2 * (0.85 + rand() * 0.2));
  return { altitudeM, rangeM, swathM };
}
