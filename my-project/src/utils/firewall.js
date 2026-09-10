// Mirrors marineguard/firewall/risk_taxonomy.py + policy.py.
// The four rows below are taken directly from the repo's stated taxonomy —
// nothing here is invented. Keep this file in sync if risk_taxonomy.py changes.

export const RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

export const RISK_TAXONOMY = [
  {
    level: "LOW",
    trigger: "confidence < 0.5, battery > 40%",
    action: "Log & continue",
  },
  {
    level: "MEDIUM",
    trigger: "confidence 0.5 – 0.75",
    action: "Trigger close inspection",
  },
  {
    level: "HIGH",
    trigger: "confidence > 0.75 OR battery < 20%",
    action: "Alert operator",
  },
  {
    level: "CRITICAL",
    trigger: "confidence > 0.9 AND comms degraded",
    action: "Emergency ascent",
  },
];

// Severity check runs most-severe-first, so an event that matches more than
// one row (e.g. very high confidence with also-low battery) is reported at
// its highest applicable level. The source doc doesn't spell out overlap
// resolution explicitly — this ordering is the natural reading of it, not
// a repo-confirmed rule, so flag it if that assumption ever needs revisiting.
export function evaluateRisk({ confidence, battery, commsDegraded }) {
  if (confidence > 0.9 && commsDegraded) {
    return { level: "CRITICAL", action: "Emergency ascent" };
  }
  if (confidence > 0.75 || battery < 20) {
    return { level: "HIGH", action: "Alert operator" };
  }
  if (confidence >= 0.5 && confidence <= 0.75) {
    return { level: "MEDIUM", action: "Trigger close inspection" };
  }
  return { level: "LOW", action: "Log & continue" };
}

export const RISK_TONE = {
  LOW: "teal",
  MEDIUM: "amber",
  HIGH: "coral",
  CRITICAL: "coral-pulse",
};
