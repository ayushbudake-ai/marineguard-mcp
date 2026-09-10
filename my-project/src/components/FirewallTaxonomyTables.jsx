import RiskBadge from "./RiskBadge";
import { RISK_TAXONOMY } from "../utils/firewall";

export default function FirewallTaxonomyTable({ activeLevel }) {
  return (
    <div className="border border-line bg-surface">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-line text-xs uppercase tracking-wide text-muted">
            <th className="px-4 py-3 font-normal">Risk level</th>
            <th className="px-4 py-3 font-normal">Trigger</th>
            <th className="px-4 py-3 font-normal">Action</th>
          </tr>
        </thead>
        <tbody>
          {RISK_TAXONOMY.map((row) => (
            <tr
              key={row.level}
              className={`border-b border-line/60 last:border-0 ${
                activeLevel === row.level ? "bg-surface2" : ""
              }`}
            >
              <td className="px-4 py-3">
                <RiskBadge level={row.level} />
              </td>
              <td className="px-4 py-3 font-mono text-xs text-muted">{row.trigger}</td>
              <td className="px-4 py-3">{row.action}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
