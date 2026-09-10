// -----------------------------------------------------------------------
// Mock evidence generator for Module 4 (Explainable Trace Engine).
// -----------------------------------------------------------------------
// There is no real sensor imagery or tracer.py output wired up yet, so
// every panel here is synthetic. Everything is seeded off the detection
// id (mulberry32 PRNG) so a given detection always renders the same
// "evidence" rather than reshuffling on every render — that consistency
// matters once this is meant to look audit-like.
//
// TODO: once tracer.py + evidence_overlay.py expose real output, replace
// buildMockEvidence() with a fetch keyed on detection id, and keep the
// return shape the same so EvidenceOverlay / ExplainableTrace don't need
// to change.
// -----------------------------------------------------------------------

function hashSeed(str) {
  let h = 1779033703 ^ str.length;
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  return () => {
    h = Math.imul(h ^ (h >>> 16), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    h ^= h >>> 16;
    return (h >>> 0) / 4294967296;
  };
}

export function buildMockEvidence(detection) {
  const rand = hashSeed(detection.id);

  // Sonar waterfall: horizontal bands with one "shadow" row where the
  // target return sits, roughly centered, width scaled by confidence.
  const sonarRows = Array.from({ length: 28 }, () => 0.15 + rand() * 0.5);
  const shadowRow = 12 + Math.floor(rand() * 4);
  const shadowWidth = 30 + detection.confidence * 40;

  // Optical bounding box, positioned with a little jitter.
  const boxX = 70 + rand() * 60;
  const boxY = 50 + rand() * 40;
  const boxW = 80 + rand() * 50;
  const boxH = 60 + rand() * 40;

  // SAM2 mask: an irregular blob roughly inside the optical bbox.
  const cx = boxX + boxW / 2;
  const cy = boxY + boxH / 2;
  const points = Array.from({ length: 10 }, (_, i) => {
    const angle = (i / 10) * Math.PI * 2;
    const r = (Math.min(boxW, boxH) / 2.4) * (0.7 + rand() * 0.5);
    return `${(cx + Math.cos(angle) * r).toFixed(1)},${(cy + Math.sin(angle) * r).toFixed(1)}`;
  });
  const maskPath = `M${points.join(" L")} Z`;

  // Bathymetry cross-section: depth profile with a protrusion near the
  // target's along-track position.
  const bumpAt = 10 + Math.floor(rand() * 10);
  const bathymetry = Array.from({ length: 30 }, (_, i) => {
    const base = 40 + Math.sin(i / 5) * 2;
    const dist = Math.abs(i - bumpAt);
    const bump = dist < 3 ? (3 - dist) * (2 + detection.confidence * 4) : 0;
    return base - bump;
  });

  // Explainable trace: a plausible per-modality reasoning chain that
  // fuses toward the detection's stored confidence. Flavor text only —
  // not a real Dempster-Shafer computation.
  const sssConf = clamp(detection.confidence + (rand() - 0.5) * 0.15);
  const opticalConf = clamp(detection.confidence + (rand() - 0.5) * 0.15);
  const bathyConf = clamp(detection.confidence + (rand() - 0.5) * 0.2);

  const traceSteps = [
    {
      title: "Side-scan sonar detector",
      detail: `Shadow signature flagged at range bin ${shadowRow}, width ${shadowWidth.toFixed(0)}px`,
      confidence: sssConf,
    },
    {
      title: "Optical detector",
      detail: `YOLOv8-style bounding box matched at overlapping coordinates`,
      confidence: opticalConf,
    },
    {
      title: "Bathymetry mapper",
      detail: `Depth protrusion of ${((3 + detection.confidence * 4) / 10).toFixed(2)}m detected at along-track bin ${bumpAt}`,
      confidence: bathyConf,
    },
    {
      title: "Fusion engine (Dempster-Shafer)",
      detail: "Combined evidence across sonar, optical, and bathymetry channels",
      confidence: detection.confidence,
    },
  ];

  return { sonarRows, shadowRow, shadowWidth, boxX, boxY, boxW, boxH, maskPath, bathymetry, traceSteps };
}

function clamp(n) {
  return Math.max(0.05, Math.min(0.99, n));
}
