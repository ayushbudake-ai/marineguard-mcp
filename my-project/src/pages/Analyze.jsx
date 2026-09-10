import { useState } from "react";
import UploadPanel from "./uploadpanel";
import ConfidenceSlider from "./confidenceslider";
import StatCard from "./statcard";
import DetectionTable from "./detectiontable";
import { uploadSurveyFile, runDetection } from "./marineguard";

export default function Analyze() {
  const [file, setFile] = useState(null);
  const [uploadedFileId, setUploadedFileId] = useState(null);
  const [threshold, setThreshold] = useState(0.5);
  const [status, setStatus] = useState("idle"); // idle | uploading | ready | processing | done
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleFileSelected(selected) {
    setFile(selected);
    setUploadedFileId(null);
    setResult(null);
    setError(null);
    setStatus("uploading");
    try {
      const uploaded = await uploadSurveyFile(selected);
      setUploadedFileId(uploaded.fileId);
      setStatus("ready");
    } catch (uploadError) {
      setStatus("idle");
      setError(uploadError instanceof Error ? uploadError.message : "Image upload failed.");
    }
  }

  async function handleRunDetection() {
    if (!uploadedFileId) return;
    setStatus("processing");
    setError(null);
    try {
      const res = await runDetection({ fileId: uploadedFileId, confidenceThreshold: threshold });
      setResult(res);
      setStatus("done");
    } catch (detectionError) {
      setStatus("ready");
      setError(detectionError instanceof Error ? detectionError.message : "Detection failed.");
    }
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
            disabled={!uploadedFileId || status === "uploading" || status === "processing"}
            className="mt-6 w-full border border-teal/60 bg-teal/10 py-2.5 text-sm text-teal transition-colors hover:bg-teal/20 disabled:cursor-not-allowed disabled:border-line disabled:bg-transparent disabled:text-muted"
          >
            {status === "uploading"
              ? "Uploading..."
              : status === "processing"
                ? "Running detection..."
                : "Run Detection"}
          </button>
        </div>
      </div>

      {error && <div className="mt-6 border border-coral bg-coral/10 px-5 py-4 text-sm text-coral">{error}</div>}

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
            <DetectionTable detections={result.detections} />
          </div>
        </>
      )}

    </div>
  );
}
