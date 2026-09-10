import SonarPanel from "./evidence/SonarPanel";
import OpticalPanel from "./evidence/OpticalPanel";
import MaskPanel from "./evidence/MaskPanel";
import BathymetryPanel from "./evidence/BathymetryPanel";

export default function EvidenceOverlay({ detection, evidence }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <SonarPanel evidence={evidence} />
      <OpticalPanel evidence={evidence} detection={detection} />
      <MaskPanel evidence={evidence} detection={detection} />
      <BathymetryPanel evidence={evidence} />
    </div>
  );
}
