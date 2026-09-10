import React, { useState, useEffect } from "react";
import UploadPanel from "../pages/uploadpanel";
import ConfidenceSlider from "../pages/confidenceslider";
import StatCard from "../pages/statcard";
import DetectionTable from "../pages/detectiontable";
import { uploadSurveyFile, runDetection, fetchDemoSamples } from "../pages/marineguard";

export default function Analyze() {
  const [inputMode, setInputMode] = useState("demo"); // demo | upload
  const [demoSamples, setDemoSamples] = useState([]);
  const [selectedSampleKey, setSelectedSampleKey] = useState("sample_01");
  const [file, setFile] = useState(null);
  const [uploadedFileId, setUploadedFileId] = useState(null);
  const [threshold, setThreshold] = useState(0.75);
  const [status, setStatus] = useState("idle"); // idle | uploading | ready | processing | done
  const [result, setResult] = useState(null);
  const [inspecting, setInspecting] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDemoSamples().then((samples) => {
      if (samples && samples.length > 0) {
        setDemoSamples(samples);
        setSelectedSampleKey(samples[0].id);
      }
    });
  }, []);

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
    setStatus("processing");
    setError(null);
    try {
      let payload = { confidenceThreshold: threshold };
      if (inputMode === "demo") {
        payload.sampleKey = selectedSampleKey;
      } else {
        if (!uploadedFileId) {
          setError("Please upload an SSS image file first.");
          setStatus("idle");
          return;
        }
        payload.fileId = uploadedFileId;
      }

      const res = await runDetection(payload);
      setResult(res);
      setStatus("done");
    } catch (detectionError) {
      setStatus("idle");
      setError(detectionError instanceof Error ? detectionError.message : "Detection failed.");
    }
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-fg">SSS AI Debris Analysis</h1>
        <p className="mt-1 text-sm text-muted">
          Execute real YOLOv8n inference on recorded Side-Scan Sonar (SSS) imagery with Role 3 post-processing.
        </p>
      </div>

      {/* Input Mode Selector */}
      <div className="mb-6 flex gap-3 border-b border-line pb-4">
        <button
          onClick={() => { setInputMode("demo"); setResult(null); }}
          className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            inputMode === "demo"
              ? "bg-teal/15 text-teal border border-teal/40"
              : "bg-surface text-muted hover:text-fg border border-line"
          }`}
        >
          Mode A: Automatic Repository Demo
        </button>
        <button
          onClick={() => { setInputMode("upload"); setResult(null); }}
          className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
            inputMode === "upload"
              ? "bg-teal/15 text-teal border border-teal/40"
              : "bg-surface text-muted hover:text-fg border border-line"
          }`}
        >
          Mode B: Manual SSS Image Upload
        </button>
      </div>

      {/* Control Panel Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Left: Data Selection */}
        <div className="border border-line bg-surface p-5 rounded-lg flex flex-col justify-between">
          {inputMode === "demo" ? (
            <div>
              <div className="mb-2 text-xs uppercase tracking-wide text-muted font-mono">
                Select Repository SSS Sample
              </div>
              <div className="space-y-3 mt-3">
                {demoSamples.map((sample) => (
                  <label
                    key={sample.id}
                    className={`flex items-start gap-3 p-3 rounded-md border cursor-pointer transition-all ${
                      selectedSampleKey === sample.id
                        ? "border-teal bg-teal/5 text-fg"
                        : "border-line bg-surface2 text-muted hover:text-fg"
                    }`}
                  >
                    <input
                      type="radio"
                      name="demo_sample"
                      value={sample.id}
                      checked={selectedSampleKey === sample.id}
                      onChange={() => setSelectedSampleKey(sample.id)}
                      className="mt-1 text-teal"
                    />
                    <div>
                      <div className="text-sm font-medium text-fg">{sample.name}</div>
                      <div className="text-xs text-muted mt-1">{sample.description}</div>
                      <div className="text-[11px] font-mono text-teal/80 mt-1">
                        GPS: {sample.has_gps ? `Recorded (${sample.lat_lon.join(", ")})` : "Unavailable (Negative/Ungeotagged)"}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          ) : (
            <div>
              <div className="mb-2 text-xs uppercase tracking-wide text-muted font-mono">
                Upload SSS Sonar Image
              </div>
              <UploadPanel
                file={file}
                onFileSelected={handleFileSelected}
                disabled={status === "processing"}
              />
            </div>
          )}
        </div>

        {/* Right: Confidence Threshold & Trigger */}
        <div className="border border-line bg-surface p-5 rounded-lg flex flex-col justify-between">
          <div>
            <div className="mb-2 text-xs uppercase tracking-wide text-muted font-mono">
              Role 3 Confidence Threshold Gating
            </div>
            <p className="text-xs text-muted mb-4">
              Detections with confidence below this threshold are marked FILTERED with justification reasons.
            </p>
            <ConfidenceSlider
              value={threshold}
              onChange={setThreshold}
              disabled={status === "processing"}
            />
          </div>

          <div className="mt-6">
            <button
              onClick={handleRunDetection}
              disabled={status === "processing" || (inputMode === "upload" && !uploadedFileId)}
              className="w-full border border-teal/60 bg-teal/20 py-3 text-sm font-semibold text-teal rounded-md transition-all hover:bg-teal/30 disabled:cursor-not-allowed disabled:border-line disabled:bg-surface2 disabled:text-muted"
            >
              {status === "processing" ? "Running Real YOLOv8n Inference…" : "🚀 Run SSS AI Detection"}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="mt-6 border border-rose-500/50 bg-rose-500/10 p-4 rounded-md text-sm text-rose-300">
          ❌ {error}
        </div>
      )}

      {/* Detection Results */}
      {result && (
        <div className="mt-10 space-y-8">
          {/* Stat Cards */}
          <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
            <StatCard label="Raw YOLO Detections" value={result.totalDetections} />
            <StatCard label="Accepted (Role 3)" value={result.acceptedCount} tone="teal" />
            <StatCard label="Filtered" value={result.filteredCount} tone="amber" />
            <StatCard
              label="Avg. Confidence"
              value={
                typeof result.averageConfidence === "number"
                  ? `${(result.averageConfidence * 100).toFixed(1)}%`
                  : "N/A"
              }
            />
            <StatCard label="Latency" value={`${result.processingTimeMs.toFixed(1)} ms`} tone="teal" />
          </div>

          {/* Visual Images Side by Side */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 border border-line bg-surface p-5 rounded-lg">
            <div>
              <div className="text-xs uppercase font-mono text-muted mb-2">Original SSS Waterfall Input</div>
              {result.originalImageUrl && (
                <img
                  src={result.originalImageUrl}
                  alt="Original SSS"
                  className="w-full h-auto rounded border border-line object-contain max-h-96 bg-black"
                />
              )}
            </div>
            <div>
              <div className="text-xs uppercase font-mono text-muted mb-2">Real YOLOv8n Bounding Box Detections</div>
              {result.annotatedImageUrl && (
                <img
                  src={result.annotatedImageUrl}
                  alt="YOLO Annotations"
                  className="w-full h-auto rounded border border-line object-contain max-h-96 bg-black"
                />
              )}
            </div>
          </div>

          {/* Detections Table */}
          <div>
            <div className="mb-2 text-xs uppercase tracking-wide text-muted font-mono">
              Detection Inventory & Role 3 Filter Justification
            </div>
            <DetectionTable detections={result.detections} onInspect={setInspecting} />
          </div>
        </div>
      )}

      {/* Inspect Modal */}
      {inspecting && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 px-4 backdrop-blur-sm"
          onClick={() => setInspecting(null)}
        >
          <div
            className="w-full max-w-lg border border-line bg-surface p-6 rounded-lg shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center border-b border-line pb-3">
              <div>
                <span className="font-mono text-xs text-muted">{inspecting.id}</span>
                <h3 className="text-lg font-bold text-fg">{inspecting.objectClass}</h3>
              </div>
              <span className={`px-2 py-1 text-xs font-mono rounded ${
                inspecting.status === "accepted" ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40" : "bg-rose-500/20 text-rose-400 border border-rose-500/40"
              }`}>
                {inspecting.status.toUpperCase()}
              </span>
            </div>

            <dl className="mt-4 space-y-3 text-sm">
              <div className="flex justify-between py-1 border-b border-line/40">
                <dt className="text-muted">Raw Neural Network Confidence</dt>
                <dd className="font-mono text-teal">{inspecting.confidencePct || `${(inspecting.confidence * 100).toFixed(1)}%`}</dd>
              </div>
              <div className="flex justify-between py-1 border-b border-line/40">
                <dt className="text-muted">Bounding Box Coordinates</dt>
                <dd className="font-mono text-xs text-fg">{inspecting.bboxCoords}</dd>
              </div>
              <div className="flex justify-between py-1 border-b border-line/40">
                <dt className="text-muted">Bounding Box Area</dt>
                <dd className="font-mono text-xs text-fg">{inspecting.bboxArea} px²</dd>
              </div>
              <div className="flex justify-between py-1 border-b border-line/40">
                <dt className="text-muted">Role 3 Verdict Reason</dt>
                <dd className="text-xs text-muted text-right max-w-xs">{inspecting.rejectionReason}</dd>
              </div>
              <div className="flex justify-between py-1 border-b border-line/40">
                <dt className="text-muted">Geodetic Location</dt>
                <dd className="font-mono text-xs text-fg">
                  {inspecting.lat && inspecting.lng ? `${inspecting.lat.toFixed(4)}, ${inspecting.lng.toFixed(4)}` : "Location Unavailable"}
                </dd>
              </div>
            </dl>

            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setInspecting(null)}
                className="px-4 py-2 bg-surface2 border border-line text-sm rounded hover:bg-surface2/80 text-fg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}