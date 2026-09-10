import React, { useState, useEffect, useRef } from "react";
import { Link } from "react-router";
import UploadPanel from "./uploadpanel";
import ConfidenceSlider from "./confidenceslider";
import StatCard from "./statcard";
import { uploadSurveyFile, runDetection, fetchDemoSamples, fetchMetrics } from "./marineguard";
import {
  ScanSearch,
  Cpu,
  ShieldCheck,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCcw,
  Sliders,
  Layers,
  ChevronRight,
  Info,
  X,
  ExternalLink,
  Sparkles,
  AlertCircle,
  Eye,
  EyeOff,
} from "lucide-react";

export default function Analyze() {
  const [inputMode, setInputMode] = useState("demo"); // demo | upload
  const [demoSamples, setDemoSamples] = useState([]);
  const [selectedSampleKey, setSelectedSampleKey] = useState("ghost_net_contact_01");
  const [file, setFile] = useState(null);
  const [uploadedFileId, setUploadedFileId] = useState(null);
  const [threshold, setThreshold] = useState(0.75);
  const [status, setStatus] = useState("idle"); // idle | uploading | processing | done
  const [result, setResult] = useState(null);
  const [selectedDetectionId, setSelectedDetectionId] = useState(null);
  const [error, setError] = useState(null);
  const [modelInfoOpen, setModelInfoOpen] = useState(false);

  // Viewer interactive state
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [showAnnotations, setShowAnnotations] = useState(true);
  const [showFiltered, setShowFiltered] = useState(true);

  const containerRef = useRef(null);

  useEffect(() => {
    fetchDemoSamples().then((samples) => {
      if (samples && samples.length > 0) {
        setDemoSamples(samples);
        const defaultSample = samples.find((s) => s.id === "ghost_net_contact_01") || samples[0];
        setSelectedSampleKey(defaultSample.id);
      }
    });
  }, []);

  // Debounced auto-re-evaluation when threshold changes while viewing existing results
  useEffect(() => {
    if (!result || status === "processing" || status === "uploading") return;
    if (result.confidenceThreshold === threshold) return;

    const timer = setTimeout(() => {
      handleRunDetection();
    }, 450);

    return () => clearTimeout(timer);
  }, [threshold]);

  // Set default selected detection when result arrives
  useEffect(() => {
    if (result && result.detections && result.detections.length > 0) {
      setSelectedDetectionId(result.detections[0].id);
    } else {
      setSelectedDetectionId(null);
    }
  }, [result]);

  async function handleFileSelected(selected) {
    setFile(selected);
    setUploadedFileId(null);
    setResult(null);
    setError(null);
    setStatus("uploading");
    try {
      const uploaded = await uploadSurveyFile(selected, threshold);
      setUploadedFileId(uploaded.fileId);
      setResult(uploaded);
      setStatus("done");
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

  function handleSelectSample(sampleId) {
    setSelectedSampleKey(sampleId);
    setResult(null);
    setError(null);
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }

  // Viewer Pan handlers
  function handleMouseDown(e) {
    if (zoom <= 1) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  }

  function handleMouseMove(e) {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  }

  function handleMouseUp() {
    setIsDragging(false);
  }

  function resetViewer() {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }

  // Find currently inspected detection
  const selectedDetection = result?.detections?.find((d) => d.id === selectedDetectionId);

  // Dynamic class counts from real inference detections
  const countNet = result?.detections?.filter((d) => d.species === "ghost_net" || d.species === "net").length ?? 0;
  const countBottle = result?.detections?.filter((d) => d.species?.includes("bottle")).length ?? 0;
  const countCan = result?.detections?.filter((d) => d.species === "can").length ?? 0;
  const countPlastic = result?.detections?.filter((d) => d.species?.includes("plastic") || d.species?.includes("container") || d.species?.includes("cup") || d.species?.includes("bag")).length ?? 0;
  const countTire = result?.detections?.filter((d) => d.species === "tire").length ?? 0;
  const countOtherDebris = result?.detections?.filter((d) => !["ghost_net", "net", "can", "tire"].includes(d.species) && !d.species?.includes("bottle") && !d.species?.includes("plastic") && !d.species?.includes("container") && !["animal", "fish", "starfish", "plant", "sponge"].includes(d.species)).length ?? 0;

  const classLegend = [
    {
      name: "Ghost Net",
      count: countNet,
      color: countNet > 0 ? "border-teal text-teal bg-teal/15 shadow-sm shadow-teal/10" : "border-teal/40 text-teal bg-teal/5",
    },
    {
      name: "Bottle",
      count: countBottle,
      color: countBottle > 0 ? "border-teal text-teal bg-teal/15 shadow-sm shadow-teal/10" : "border-line text-muted bg-surface2/40",
    },
    {
      name: "Can",
      count: countCan,
      color: countCan > 0 ? "border-teal text-teal bg-teal/15 shadow-sm shadow-teal/10" : "border-line text-muted bg-surface2/40",
    },
    {
      name: "Plastic",
      count: countPlastic,
      color: countPlastic > 0 ? "border-teal text-teal bg-teal/15 shadow-sm shadow-teal/10" : "border-line text-muted bg-surface2/40",
    },
    {
      name: "Tire",
      count: countTire,
      color: countTire > 0 ? "border-teal text-teal bg-teal/15 shadow-sm shadow-teal/10" : "border-line text-muted bg-surface2/40",
    },
    {
      name: "Other Debris",
      count: countOtherDebris,
      color: countOtherDebris > 0 ? "border-teal text-teal bg-teal/15 shadow-sm shadow-teal/10" : "border-line text-muted bg-surface2/40",
    },
  ];

  return (
    <div className="max-w-[1600px] mx-auto space-y-6 pb-12">
      {/* ------------------------------------------------------------- */}
      {/* HEADER & UNIFIED MODEL BADGE */}
      {/* ------------------------------------------------------------- */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-line pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-fg">SSS MODEL</h1>
            <span className="flex items-center gap-1.5 rounded-full border border-teal/40 bg-teal/10 px-2.5 py-0.5 font-mono text-[11px] text-teal">
              <span className="h-1.5 w-1.5 rounded-full bg-teal animate-pulse" />
              READY
            </span>
          </div>
          <p className="text-xs text-muted font-mono mt-0.5">
            Unified Side-Scan Sonar Detection Engine · Role 3 Gating Active
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setModelInfoOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-line bg-surface hover:border-teal/50 text-xs font-mono text-fg transition-all shadow-sm"
          >
            <Info size={14} className="text-teal" />
            Model Information
          </button>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* 3-COLUMN SCIENTIFIC DEEP-OCEAN WORKBENCH */}
      {/* ------------------------------------------------------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* ========================================================= */}
        {/* LEFT COLUMN: Controls & Ingestion (Cols: 3 / 12) */}
        {/* ========================================================= */}
        <div className="lg:col-span-3 space-y-5">
          {/* Mode Selector */}
          <div className="flex rounded-lg border border-line bg-surface/80 p-1">
            <button
              onClick={() => { setInputMode("demo"); setResult(null); setError(null); }}
              className={`flex-1 py-1.5 text-xs font-mono font-medium rounded-md transition-all ${
                inputMode === "demo"
                  ? "bg-teal/20 text-teal border border-teal/40 shadow-sm"
                  : "text-muted hover:text-fg"
              }`}
            >
              Demo Samples
            </button>
            <button
              onClick={() => { setInputMode("upload"); setResult(null); setError(null); }}
              className={`flex-1 py-1.5 text-xs font-mono font-medium rounded-md transition-all ${
                inputMode === "upload"
                  ? "bg-teal/20 text-teal border border-teal/40 shadow-sm"
                  : "text-muted hover:text-fg"
              }`}
            >
              Upload SSS
            </button>
          </div>

          {/* Ingestion Panel */}
          <div className="rounded-xl border border-line bg-surface/70 backdrop-blur p-5 shadow-lg shadow-black/20 space-y-4">
            {inputMode === "demo" ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs font-mono text-muted uppercase tracking-wider">
                  <span>Repository SSS Scans</span>
                  <span className="text-[10px] text-teal">{demoSamples.length} samples</span>
                </div>

                <div className="space-y-2.5">
                  {demoSamples.map((sample) => {
                    const isSelected = selectedSampleKey === sample.id;
                    return (
                      <div
                        key={sample.id}
                        onClick={() => handleSelectSample(sample.id)}
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${
                          isSelected
                            ? "border-teal bg-teal/10 shadow-sm shadow-teal/10"
                            : "border-line bg-surface2/50 hover:bg-surface2 hover:border-line/80 text-muted"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className={`text-xs font-medium ${isSelected ? "text-fg" : "text-fg/80"}`}>
                            {sample.name}
                          </span>
                          {isSelected && <span className="h-1.5 w-1.5 rounded-full bg-teal" />}
                        </div>
                        <p className="text-[11px] text-muted mt-1 leading-snug line-clamp-2">
                          {sample.description}
                        </p>
                        <div className="mt-2 flex items-center justify-between font-mono text-[10px]">
                          <span className="text-muted">{sample.sensor || "Side-Scan Sonar"}</span>
                          <span className={sample.has_gps ? "text-teal" : "text-muted"}>
                            {sample.has_gps ? "GPS Tracked" : "No GPS"}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="text-xs font-mono text-muted uppercase tracking-wider">
                  Upload Recorded SSS Waterfall
                </div>
                <UploadPanel
                  file={file}
                  onFileSelected={handleFileSelected}
                  disabled={status === "processing" || status === "uploading"}
                />
              </div>
            )}
          </div>

          {/* Role 3 Gating Threshold Panel */}
          <div className="rounded-xl border border-line bg-surface/70 backdrop-blur p-5 shadow-lg shadow-black/20 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-muted uppercase tracking-wider flex items-center gap-1.5">
                <Sliders size={13} className="text-teal" /> Role 3 Threshold
              </span>
              <span className="font-mono text-xs font-bold text-teal bg-teal/10 border border-teal/30 px-2 py-0.5 rounded">
                {(threshold * 100).toFixed(0)}%
              </span>
            </div>

            <p className="text-[11px] text-muted leading-relaxed">
              Confidence gating applied by Role 3. Proposals below threshold are marked FILTERED with justification.
            </p>

            <ConfidenceSlider
              value={threshold}
              onChange={setThreshold}
              disabled={status === "processing"}
            />

            {result && Math.abs(result.confidenceThreshold - threshold) > 0.001 && (
              <div className="text-[11px] font-mono text-amber flex items-center gap-1.5 animate-pulse">
                <AlertCircle size={12} /> Auto-updating Role 3 filter...
              </div>
            )}
          </div>

          {/* Primary Action Button */}
          <button
            onClick={handleRunDetection}
            disabled={status === "processing" || status === "uploading" || (inputMode === "upload" && !uploadedFileId)}
            className="w-full relative group overflow-hidden rounded-xl border border-teal/60 bg-gradient-to-r from-teal/25 via-cyan-500/20 to-teal/25 p-3.5 text-center font-mono text-xs font-bold uppercase tracking-wider text-fg shadow-lg shadow-teal/10 transition-all hover:bg-teal/30 hover:border-teal disabled:cursor-not-allowed disabled:border-line disabled:bg-surface2 disabled:text-muted"
          >
            <div className="flex items-center justify-center gap-2">
              {status === "processing" ? (
                <>
                  <span className="h-2 w-2 rounded-full bg-teal animate-ping" />
                  <span>Processing Waterfall Sonar…</span>
                </>
              ) : status === "uploading" ? (
                <span>Ingesting Sonar Bytes…</span>
              ) : (
                <>
                  <ScanSearch size={16} className="text-teal" />
                  <span>Run SSS Analysis</span>
                </>
              )}
            </div>
          </button>

          {error && (
            <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-3 text-xs text-rose-300 font-mono">
              ⚠️ {error}
            </div>
          )}
        </div>

        {/* ========================================================= */}
        {/* CENTER COLUMN: Large SSS Image Viewer (Cols: 6 / 12) */}
        {/* ========================================================= */}
        <div className="lg:col-span-6 space-y-4">
          <div className="rounded-xl border border-line bg-surface/70 backdrop-blur shadow-lg shadow-black/20 overflow-hidden">
            {/* Viewer Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-2.5 bg-surface2/40 font-mono text-xs">
              <div className="flex items-center gap-3">
                <span className="text-muted uppercase text-[10px] tracking-wider">Viewport</span>
                <span className="text-fg font-semibold truncate max-w-xs">
                  {result ? (result.sampleName || result.fileId) : "No Scan Loaded"}
                </span>
                {result?.imageShape && (
                  <span className="text-muted text-[11px]">
                    ({result.imageShape[1]} × {result.imageShape[0]} px)
                  </span>
                )}
              </div>

              {/* Viewport Control Buttons */}
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => setShowAnnotations(!showAnnotations)}
                  className={`px-2 py-1 rounded text-[11px] font-mono border flex items-center gap-1 ${
                    showAnnotations
                      ? "border-teal/50 bg-teal/15 text-teal"
                      : "border-line bg-surface2 text-muted"
                  }`}
                  title="Toggle Neural Bounding Boxes"
                >
                  {showAnnotations ? <Eye size={12} /> : <EyeOff size={12} />}
                  <span>Boxes</span>
                </button>

                <div className="h-3 w-px bg-line mx-1" />

                <button
                  onClick={() => setZoom((z) => Math.min(4, z + 0.25))}
                  className="p-1.5 rounded border border-line bg-surface2 hover:bg-surface text-muted hover:text-fg"
                  title="Zoom In"
                >
                  <ZoomIn size={13} />
                </button>
                <button
                  onClick={() => setZoom((z) => Math.max(1, z - 0.25))}
                  className="p-1.5 rounded border border-line bg-surface2 hover:bg-surface text-muted hover:text-fg"
                  title="Zoom Out"
                >
                  <ZoomOut size={13} />
                </button>
                <button
                  onClick={resetViewer}
                  className="p-1.5 rounded border border-line bg-surface2 hover:bg-surface text-muted hover:text-fg"
                  title="Reset 1:1"
                >
                  <RotateCcw size={13} />
                </button>

                <span className="font-mono text-[10px] text-muted ml-1">{Math.round(zoom * 100)}%</span>
              </div>
            </div>

            {/* Main Interactive Image Viewport */}
            <div
              ref={containerRef}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              className="relative w-full h-[520px] bg-black/90 flex items-center justify-center overflow-hidden select-none cursor-grab active:cursor-grabbing"
            >
              {/* Sonar Grid Overlay Lines */}
              <div className="absolute inset-0 pointer-events-none opacity-20 bg-[linear-gradient(to_right,#20343c_1px,transparent_1px),linear-gradient(to_bottom,#20343c_1px,transparent_1px)] bg-[size:40px_40px]" />

              {/* Range Scale Markers */}
              <div className="absolute left-2 top-2 bottom-2 w-6 pointer-events-none flex flex-col justify-between text-[9px] font-mono text-teal/40">
                <span>0m</span>
                <span>20m</span>
                <span>40m</span>
                <span>60m</span>
              </div>

              {result ? (
                <div
                  style={{
                    transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                    transition: isDragging ? "none" : "transform 0.15s ease-out",
                  }}
                  className="relative max-h-full max-w-full flex items-center justify-center"
                >
                  <img
                    src={showAnnotations ? (result.annotatedImageUrl || result.originalImageUrl) : result.originalImageUrl}
                    alt="Side-Scan Sonar"
                    className="max-h-[500px] w-auto object-contain rounded shadow-2xl pointer-events-none"
                  />
                </div>
              ) : (
                <div className="text-center space-y-2 p-6">
                  <div className="inline-flex p-3 rounded-full bg-teal/10 text-teal mb-2">
                    <ScanSearch size={32} />
                  </div>
                  <h3 className="font-mono text-sm font-semibold text-fg">Awaiting SSS Imagery</h3>
                  <p className="text-xs text-muted max-w-xs mx-auto">
                    Select a repository demo sample on the left or upload an SSS waterfall file to initiate real neural inference.
                  </p>
                </div>
              )}
            </div>

            {/* Viewport Footer Metadata */}
            {result && (
              <div className="px-4 py-2.5 border-t border-line bg-surface2/30 flex flex-wrap items-center justify-between gap-2 font-mono text-xs">
                <span className="text-muted">
                  GPS:{" "}
                  <span className={result.hasGps ? "text-emerald-400" : "text-amber"}>
                    {result.hasGps && result.gpsCoordinates
                      ? `Recorded (${result.gpsCoordinates[0].toFixed(4)}, ${result.gpsCoordinates[1].toFixed(4)})`
                      : "Geolocation unavailable — no recorded coordinates supplied"}
                  </span>
                </span>
                <span className="text-muted">
                  Raw neural avg:{" "}
                  <span className="text-teal">
                    {result.totalDetections > 0 && typeof result.averageConfidence === "number"
                      ? `${(result.averageConfidence * 100).toFixed(1)}%`
                      : "0.0%"}
                  </span>
                </span>
              </div>
            )}
          </div>

          {/* Supported SSS Classes Legend */}
          <div className="rounded-xl border border-line bg-surface/70 backdrop-blur p-4 shadow-lg shadow-black/20">
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-xs font-mono text-muted uppercase tracking-wider flex items-center gap-1.5">
                <Layers size={13} className="text-teal" /> Monitored Debris Taxonomy
              </span>
              <span className="text-[10px] font-mono text-muted">Authoritative Model Names</span>
            </div>

            <div className="flex flex-wrap gap-2">
              {classLegend.map((cls) => {
                const hasDetections = cls.count > 0;
                return (
                  <div
                    key={cls.name}
                    className={`px-2.5 py-1 rounded-lg border text-xs font-mono flex items-center gap-2 ${cls.color}`}
                    title={`${cls.name} monitored by unified 50-class SSS MODEL engine`}
                  >
                    <span>{cls.name}</span>
                    <span
                      className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${
                        hasDetections ? "bg-teal/30 text-teal" : "bg-surface2 text-muted"
                      }`}
                    >
                      {hasDetections ? `${cls.count} found` : "ACTIVE"}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* ========================================================= */}
        {/* RIGHT COLUMN: Detection Inspector (Cols: 3 / 12) */}
        {/* ========================================================= */}
        <div className="lg:col-span-3 space-y-5">
          {/* Quick Metrics */}
          <div className="grid grid-cols-2 gap-2.5">
            <div className="border border-line bg-surface/70 backdrop-blur p-3 rounded-xl">
              <div className="text-[10px] font-mono text-muted uppercase">Raw Detections</div>
              <div className="text-xl font-bold font-mono text-fg mt-1">
                {result ? result.totalDetections : "—"}
              </div>
            </div>
            <div className="border border-line bg-surface/70 backdrop-blur p-3 rounded-xl">
              <div className="text-[10px] font-mono text-teal uppercase">Role 3 Accepted</div>
              <div className="text-xl font-bold font-mono text-teal mt-1">
                {result ? result.acceptedCount : "—"}
              </div>
            </div>
          </div>

          {/* Detection Selection List */}
          <div className="rounded-xl border border-line bg-surface/70 backdrop-blur p-4 shadow-lg shadow-black/20 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono text-muted uppercase tracking-wider">
              <span>Detected Targets</span>
              <span className="text-teal font-bold">{result?.detections?.length ?? 0}</span>
            </div>

            {result && result.detections && result.detections.length > 0 ? (
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {result.detections.map((d) => {
                  const isSelected = d.id === selectedDetectionId;
                  const isAccepted = d.status === "accepted";
                  return (
                    <div
                      key={d.id}
                      onClick={() => setSelectedDetectionId(d.id)}
                      className={`p-2.5 rounded-lg border cursor-pointer font-mono text-xs transition-all flex items-center justify-between ${
                        isSelected
                          ? "border-teal bg-teal/15 text-fg shadow-sm shadow-teal/10"
                          : "border-line bg-surface2/50 text-muted hover:bg-surface2 hover:text-fg"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className={`h-2 w-2 rounded-full ${isAccepted ? "bg-teal" : "bg-amber"}`} />
                        <span className="font-semibold text-fg">{d.id}</span>
                        <span className="text-[11px] text-muted">{d.objectClass}</span>
                      </div>
                      <span className="text-xs text-teal">{d.confidencePct}</span>
                    </div>
                  );
                })}
              </div>
            ) : result && result.totalDetections === 0 ? (
              <div className="p-4 rounded-lg bg-surface2/40 border border-line text-center text-xs text-muted font-mono">
                Negative seabed contact · 0 targets
              </div>
            ) : (
              <div className="p-4 rounded-lg bg-surface2/40 border border-line text-center text-xs text-muted font-mono">
                No active scan result
              </div>
            )}
          </div>

          {/* Inspector Detail Card */}
          {selectedDetection ? (
            <div className="rounded-xl border border-line bg-surface/70 backdrop-blur p-5 shadow-lg shadow-black/20 space-y-4">
              <div className="flex items-start justify-between border-b border-line/60 pb-3">
                <div>
                  <span className="font-mono text-[10px] text-muted">{selectedDetection.id}</span>
                  <h3 className="text-base font-bold text-fg">{selectedDetection.objectClass}</h3>
                </div>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border uppercase ${
                    selectedDetection.status === "accepted"
                      ? "bg-teal/15 text-teal border-teal/40"
                      : "bg-amber/15 text-amber border-amber/40"
                  }`}
                >
                  {selectedDetection.status}
                </span>
              </div>

              <div className="space-y-2.5 font-mono text-xs">
                <div className="flex justify-between py-1 border-b border-line/40">
                  <span className="text-muted">Neural Confidence:</span>
                  <span className="text-teal font-bold">{selectedDetection.confidencePct}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-line/40">
                  <span className="text-muted">Role 3 Threshold:</span>
                  <span className="text-amber">{(threshold * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between py-1 border-b border-line/40">
                  <span className="text-muted">Gating Rationale:</span>
                  <span className="text-[11px] text-fg/90 text-right max-w-[140px] truncate" title={selectedDetection.rejectionReason}>
                    {selectedDetection.rejectionReason}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-line/40">
                  <span className="text-muted">Bounding Box:</span>
                  <span className="text-fg text-[11px]">{selectedDetection.bboxCoords}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-line/40">
                  <span className="text-muted">Box Area:</span>
                  <span className="text-fg">{Math.round(selectedDetection.bboxArea)} px²</span>
                </div>
                <div className="flex justify-between py-1 border-b border-line/40">
                  <span className="text-muted">Recorded GPS:</span>
                  <span className="text-fg text-[11px]">
                    {selectedDetection.lat && selectedDetection.lng
                      ? `${selectedDetection.lat.toFixed(4)}, ${selectedDetection.lng.toFixed(4)}`
                      : "Unavailable"}
                  </span>
                </div>
              </div>

              <Link
                to={`/evidence/${selectedDetection.id}`}
                className="mt-3 flex items-center justify-center gap-1.5 w-full py-2 rounded-lg border border-teal/40 bg-teal/10 hover:bg-teal/20 text-xs font-mono text-teal transition-all"
              >
                <span>Audit in Evidence Review</span>
                <ExternalLink size={12} />
              </Link>
            </div>
          ) : (
            <div className="rounded-xl border border-line bg-surface/40 p-6 text-center text-xs text-muted font-mono">
              Select a target above to inspect bounding box parameters and Role 3 rationale.
            </div>
          )}

          {/* Section 19: Collapsible Runtime Inference Trace */}
          {result && (
            <details className="rounded-xl border border-line bg-surface/70 backdrop-blur p-4 font-mono text-xs text-muted group">
              <summary className="cursor-pointer font-semibold text-fg flex items-center justify-between select-none">
                <span className="flex items-center gap-1.5 text-xs text-teal font-sans font-bold">
                  <span>⚙️</span>
                  <span>SIH Runtime Trace</span>
                </span>
                <span className="text-[10px] text-muted">details</span>
              </summary>
              <div className="mt-3 pt-3 border-t border-line/60 space-y-1.5 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-muted">Model:</span>
                  <span className="text-fg">{result.modelUsed || "SSS MODEL"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">SHA-256:</span>
                  <span className="text-fg">{result.modelSha256 ? `${result.modelSha256.substring(0, 10)}…` : "c9fd2794…"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">PyTorch Speed:</span>
                  <span className="text-teal">
                    {result.inferenceSpeedMs ? `${result.inferenceSpeedMs.toFixed(1)} ms` : "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted">Total Request:</span>
                  <span className="text-teal">
                    {result.processingTimeMs ? `${result.processingTimeMs.toFixed(1)} ms` : "—"}
                  </span>
                </div>
              </div>
            </details>
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* MODEL INFORMATION MODAL */}
      {/* ------------------------------------------------------------- */}
      {modelInfoOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-line bg-surface p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-start justify-between border-b border-line pb-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-teal/10 p-2.5 text-teal border border-teal/30">
                  <Cpu size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-fg">SSS MODEL Architecture & Specification</h3>
                  <p className="text-xs text-muted font-mono">Unified Side-Scan Sonar Detection Engine</p>
                </div>
              </div>
              <button
                onClick={() => setModelInfoOpen(false)}
                className="rounded p-1 text-muted hover:bg-surface2 hover:text-fg"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between py-1 border-b border-line/50">
                <span className="text-muted">Model Name:</span>
                <span className="text-teal font-bold">SSS MODEL</span>
              </div>
              <div className="flex justify-between py-1 border-b border-line/50">
                <span className="text-muted">Input:</span>
                <span className="text-fg">Side-Scan Sonar Analysis</span>
              </div>
              <div className="flex justify-between py-1 border-b border-line/50">
                <span className="text-muted">Detection Engine:</span>
                <span className="text-fg">Unified MarineGuard Detector</span>
              </div>
              <div className="flex justify-between py-1 border-b border-line/50">
                <span className="text-muted">Classes:</span>
                <span className="text-teal font-bold">50</span>
              </div>
              <div className="flex justify-between py-1 border-b border-line/50">
                <span className="text-muted">Filtering:</span>
                <span className="text-fg">Role 3 DetectionFilter</span>
              </div>
              <div className="flex justify-between py-1 border-b border-line/50">
                <span className="text-muted">Geodetic Location:</span>
                <span className="text-fg">Recorded SSS metadata only (Strictly No Mock GPS)</span>
              </div>
            </div>

            <div className="rounded-lg bg-surface2/60 border border-line p-3 text-xs leading-relaxed space-y-1 font-sans text-muted">
              <p className="font-semibold text-fg font-mono text-[11px] uppercase">
                Ethical AI & Data Integrity Principle:
              </p>
              <p>
                The unified <b>SSS MODEL</b> integrates the broader MarineGuard detection capability spanning 50 marine debris and fauna classes (including Bottle, Can, Plastic, Tire, Other Debris, Net, and Benthic features). The detector operates as a unified reference engine. Genuine Side-Scan Sonar benchmarks are evaluated distinctly from optical underwater training splits.
              </p>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setModelInfoOpen(false)}
                className="px-4 py-2 text-xs font-medium rounded-lg bg-teal text-ink font-semibold hover:bg-teal/90 transition-colors"
              >
                Acknowledge & Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
