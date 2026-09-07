import json
import time
from pathlib import Path

from marineguard.v1_detector import MarineGuardV1Detector


detector = MarineGuardV1Detector()

images = list(
    Path(r"data\processed\marineguard\images\test").glob("*")
)[:20]

if not images:
    raise RuntimeError("No test images found.")

print("IMAGES:", len(images))

# Warm-up
detector.predict(images[0], confidence=0.25)

latencies_ms = []

for image in images:
    start = time.perf_counter()

    detector.predict(
        image,
        confidence=0.25,
    )

    elapsed_ms = (time.perf_counter() - start) * 1000
    latencies_ms.append(elapsed_ms)

total_sec = sum(latencies_ms) / 1000
average_ms = sum(latencies_ms) / len(latencies_ms)
minimum_ms = min(latencies_ms)
maximum_ms = max(latencies_ms)
images_per_sec = len(images) / total_sec

benchmark = {
    "model_version": "v1",
    "image_size": 512,
    "confidence_threshold": 0.25,
    "images_tested": len(images),
    "total_inference_time_sec": round(total_sec, 4),
    "average_latency_ms": round(average_ms, 2),
    "min_latency_ms": round(minimum_ms, 2),
    "max_latency_ms": round(maximum_ms, 2),
    "images_per_second": round(images_per_sec, 2),
}

output_path = Path("v1_latency_benchmark.json")

output_path.write_text(
    json.dumps(benchmark, indent=2),
    encoding="utf-8",
)

print()
print("V1 LATENCY BENCHMARK")
print("=====================")
print(f"Average latency : {average_ms:.2f} ms")
print(f"Minimum latency : {minimum_ms:.2f} ms")
print(f"Maximum latency : {maximum_ms:.2f} ms")
print(f"Throughput      : {images_per_sec:.2f} images/sec")
print()
print(f"Saved to: {output_path}")
