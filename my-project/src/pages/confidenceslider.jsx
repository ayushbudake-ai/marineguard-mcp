export default function ConfidenceSlider({ value, onChange, disabled }) {
  return (
    <div className="w-full">
      <div className="mb-2 flex items-baseline justify-between">
        <label htmlFor="confidence" className="text-xs uppercase tracking-wide text-muted">
          Confidence threshold
        </label>
        <span className="font-mono text-sm text-teal">{value.toFixed(2)}</span>
      </div>
      <input
        id="confidence"
        type="range"
        min={0}
        max={1}
        step={0.01}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-1 w-full cursor-pointer appearance-none bg-line accent-teal disabled:cursor-not-allowed disabled:opacity-50"
      />
      <div className="mt-1 flex justify-between font-mono text-[10px] text-muted">
        <span>0.00</span>
        <span>1.00</span>
      </div>
    </div>
  );
}