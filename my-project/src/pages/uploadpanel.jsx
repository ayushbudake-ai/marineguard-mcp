import { useRef, useState, useEffect } from "react";

const ACCEPTED_EXTENSIONS = [
  ".png",
  ".jpg",
  ".jpeg",
  ".bmp",
  ".tif",
  ".tiff",
];

export default function UploadPanel({ file, onFileSelected, disabled }) {
  const inputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function validateAndSet(candidate) {
    if (!candidate) return;
    const nameLower = candidate.name.toLowerCase();
    const ok = ACCEPTED_EXTENSIONS.some((ext) => nameLower.endsWith(ext));
    if (!ok) {
      setError(`Unsupported file format. Expected SSS image: ${ACCEPTED_EXTENSIONS.join(", ")}`);
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
        className={`flex cursor-pointer flex-col items-center justify-center border border-dashed p-6 text-center transition-colors rounded-lg ${
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
          <div className="w-full text-center">
            {previewUrl && (
              <div className="mb-3 flex justify-center">
                <img
                  src={previewUrl}
                  alt="SSS Upload Preview"
                  className="max-h-48 rounded border border-line object-contain bg-black"
                />
              </div>
            )}
            <div className="font-mono text-sm font-semibold text-fg">{file.name}</div>
            <div className="mt-1 text-xs text-muted">
              {(file.size / 1024).toFixed(1)} KB — SSS Sonar Image Loaded
            </div>
            <div className="mt-2 text-[11px] text-teal">Click or drop to replace image</div>
          </div>
        ) : (
          <div className="py-6">
            <div className="text-2xl mb-2">📁</div>
            <div className="text-sm font-medium text-fg">Drop recorded SSS sonar image here</div>
            <div className="mt-1 text-xs text-muted">
              or click to browse — {ACCEPTED_EXTENSIONS.join(", ")}
            </div>
          </div>
        )}
      </div>
      {error && <div className="mt-2 text-xs text-coral">{error}</div>}
    </div>
  );
}