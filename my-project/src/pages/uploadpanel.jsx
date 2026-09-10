import { useRef, useState } from "react";

const ACCEPTED_EXTENSIONS = [
  ".xtf",
  ".sio",
  ".jsf",
  ".tif",
  ".tiff",
  ".jpg",
  ".jpeg",
  ".png",
]; // TODO: confirm actual supported sonar/underwater formats against the pipeline

export default function UploadPanel({ file, onFileSelected, disabled }) {
  const inputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);

  function validateAndSet(candidate) {
    if (!candidate) return;
    const nameLower = candidate.name.toLowerCase();
    const ok = ACCEPTED_EXTENSIONS.some((ext) => nameLower.endsWith(ext));
    if (!ok) {
      setError(`Unsupported file type. Expected one of: ${ACCEPTED_EXTENSIONS.join(", ")}`);
      return;
    }
    setError(null);
    onFileSelected(candidate);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragActive(false);
    if (disabled) return;
    validateAndSet(e.dataTransfer.files?.[0]);
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center border border-dashed px-6 py-10 text-center transition-colors ${
          dragActive ? "border-teal bg-teal/5" : "border-line bg-surface"
        } ${disabled ? "cursor-not-allowed opacity-50" : "hover:border-teal/60"}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(",")}
          className="hidden"
          disabled={disabled}
          onClick={(e) => e.stopPropagation()}
          onChange={(e) => validateAndSet(e.target.files?.[0])}
        />
        {file ? (
          <div className="font-mono text-sm text-fg">
            {file.name}
            <div className="mt-1 text-xs text-muted">{(file.size / 1024).toFixed(1)} KB — ready</div>
          </div>
        ) : (
          <div>
            <div className="text-sm text-fg">Drop underwater survey data here</div>
            <div className="mt-1 text-xs text-muted">or click to browse — {ACCEPTED_EXTENSIONS.join(", ")}</div>
          </div>
        )}
      </div>
      {error && <div className="mt-2 text-xs text-coral">{error}</div>}
    </div>
  );
}