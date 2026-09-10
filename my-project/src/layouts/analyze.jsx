import { useState } from "react";
import UploadPanel from "../pages/uploadpanel";
import ConfidenceSlider from "../pages/confidenceslider";
import StatCard from "../pages/statcard";
import DetectionTable from "../pages/detectiontable";
import { uploadSurveyFile, runDetection } from "../pages/marineguard";

export default function Analyze() {
  const [file, setFile] = useState(null);
  const [threshold, setThreshold] = useState(0.5);
  const [status, setStatus] = useState("idle"); // idle | uploading | ready | processing | done
  const [result, setResult] = useState(null);
  const [inspecting, setInspecting] = useState(null);

  async function handleFileSelected(selected) {
    setFile(selected);
    setResult(null);
    setStatus("uploading");
    await uploadSurveyFile(selected);
    setStatus("ready");
  }

  async function handleRunDetection() {
    if (!file) return;
    setStatus("processing");
    const res = await runDetection({ fileId: file.name, confidenceThreshold: threshold });
    setResult(res);
    setStatus("done");
  }

  return (
    <div className="max-w-4xl">
      <h1 className="text-xl text-fg">Analyze</h1>
      <p className="mt-1 text-sm text-muted">
        Upload underwater survey data, set a confidence threshold, and run the detection pipeline.
      </p>

      <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
        <div>
          <div className="mb-2 text-xs uppercase tracking-wide text-muted">Survey data</div>
          <UploadPanel file={file} onFileSelected={handleFileSelected} disabled={status === "processing"} />
        </div>
        <div className="flex flex-col justify-between border border-line bg-surface px-5 py-5">
          <ConfidenceSlider value={threshold} onChange={setThreshold} disabled={status === "processing"} />
          <button
            onClick={handleRunDetection}
            disabled={!file || status === "uploading" || status === "processing"}
            className="mt-6 w-full border border-teal/60 bg-teal/10 py-2.5 text-sm text-teal transition-colors hover:bg-teal/20 disabled:cursor-not-allowed disabled:border-line disabled:bg-transparent disabled:text-muted"
          >
            {status === "processing" ? "Running detection…" : "Run Detection"}
          </button>
        </div>
      </div>

      {status === "processing" && (
        <div className="mt-6 border border-line bg-surface px-5 py-4 text-sm text-muted">
          Processing survey data through the detection pipeline…
        </div>
      )}

      {result && (
        <>
          <div className="mt-10 grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label="Total detections" value={result.totalDetections} />
            <StatCard label="Accepted" value={result.acceptedCount} tone="teal" />
            <StatCard label="Filtered" value={result.filteredCount} tone="amber" />
            <StatCard label="Avg. confidence" value={result.averageConfidence.toFixed(2)} />
          </div>

          <div className="mt-8">
            <div className="mb-2 text-xs uppercase tracking-wide text-muted">Detections</div>
            <DetectionTable detections={result.detections} onInspect={setInspecting} />
          </div>
        </>
      )}

      {inspecting && (
        <div
          className="fixed inset-0 flex items-center justify-center bg-ink/80 px-4"
          onClick={() => setInspecting(null)}
        >
          <div
            className="w-full max-w-md border border-line bg-surface2 px-6 py-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="font-mono text-xs text-muted">{inspecting.id}</div>
            <div className="mt-1 text-lg text-fg">{inspecting.objectClass}</div>
            <dl className="mt-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted">Confidence</dt>
                <dd className="font-mono">{inspecting.confidence.toFixed(2)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">Coordinates</dt>
                <dd className="font-mono">{inspecting.lat.toFixed(4)}, {inspecting.lng.toFixed(4)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">Timestamp</dt>
                <dd className="font-mono text-xs">{new Date(inspecting.timestamp).toLocaleString()}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">Status</dt>
                <dd className="font-mono uppercase text-teal">{inspecting.status}</dd>
              </div>
            </dl>
            <button
              onClick={() => setInspecting(null)}
              className="mt-6 w-full border border-line py-2 text-sm text-muted hover:text-fg"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}