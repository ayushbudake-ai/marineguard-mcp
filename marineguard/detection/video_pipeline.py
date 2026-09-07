"""
Video & Stream Detection Pipeline for MarineGuard MCP — Role 2: AI Inference & Integration

Processes video files or live camera/ROV streams frame-by-frame:
    Video Input / Stream
    ↓
    Frame Extraction
    ↓
    Detection Pipeline
    ↓
    Frame Results Aggregator
    ↓
    (Optional) Annotated Video Output
"""

from pathlib import Path
from typing import Generator, List, Dict, Any, Optional, Union, Tuple
import numpy as np
from PIL import Image

from marineguard.detection.schema import DetectionResult
from marineguard.detection.pipeline import ImageDetectionPipeline
from marineguard.detection.annotator import ImageAnnotator


class VideoDetectionPipeline:
    """Processes video streams or files frame-by-frame with optional annotated output."""

    def __init__(
        self,
        pipeline: Optional[ImageDetectionPipeline] = None,
        annotator: Optional[ImageAnnotator] = None,
    ):
        self.pipeline = pipeline if pipeline is not None else ImageDetectionPipeline()
        self.annotator = annotator if annotator is not None else ImageAnnotator()

    def process_frame(self, frame: np.ndarray) -> DetectionResult:
        """Processes a single numpy video frame."""
        return self.pipeline.process(frame)

    def process_frame_stream(
        self,
        frames: Generator[np.ndarray, None, None],
    ) -> Generator[Tuple[DetectionResult, Optional[Image.Image]], None, None]:
        """Generator that yields (DetectionResult, annotated_frame) for every frame in a stream."""
        for frame in frames:
            result = self.process_frame(frame)
            annotated = self.annotator.annotate(frame, result)
            yield result, annotated

    def process_video_file(
        self,
        video_path: Union[str, Path],
        output_annotated_path: Optional[Union[str, Path]] = None,
        frame_stride: int = 1,
        max_frames: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Extracts frames from a video file, runs detection, and aggregates results.

        Args:
            video_path: Path to input video file.
            output_annotated_path: Optional destination for annotated output.
            frame_stride: Process every Nth frame (default: 1 = every frame).
            max_frames: Optional limit on number of frames to process.

        Returns:
            Dict containing video summary and per-frame detection results.
        """
        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: '{path}'")

        try:
            import cv2
        except ImportError:
            # Provide pure-python fallback for environments without cv2 binaries
            raise RuntimeError("OpenCV (cv2) is required for video file decoding.")

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise ValueError(f"Failed to open video file: '{path}'")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        writer = None
        if output_annotated_path is not None and width > 0 and height > 0:
            out_p = Path(output_annotated_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            writer = cv2.VideoWriter(str(out_p), fourcc, fps / frame_stride, (width, height))

        frame_idx = 0
        processed_count = 0
        frame_results: List[Dict[str, Any]] = []
        total_detections = 0

        try:
            while cap.isOpened():
                ret, frame_bgr = cap.read()
                if not ret or frame_bgr is None:
                    break

                if frame_idx % frame_stride == 0:
                    # Convert BGR to RGB for pipeline
                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    res = self.process_frame(frame_rgb)

                    frame_results.append({
                        "frame_index": frame_idx,
                        "timestamp_s": round(frame_idx / fps, 3),
                        "count": res.count,
                        "detections": [d.to_dict() for d in res.detections],
                    })
                    total_detections += res.count
                    processed_count += 1

                    if writer is not None:
                        annotated_pil = self.annotator.annotate(frame_rgb, res)
                        annotated_bgr = cv2.cvtColor(np.array(annotated_pil), cv2.COLOR_RGB2BGR)
                        writer.write(annotated_bgr)

                    if max_frames is not None and processed_count >= max_frames:
                        break

                frame_idx += 1
        finally:
            cap.release()
            if writer is not None:
                writer.release()

        return {
            "video_path": str(path),
            "total_frames_in_file": total_frames,
            "processed_frames": processed_count,
            "total_detections": total_detections,
            "frame_results": frame_results,
            "annotated_output_path": str(output_annotated_path) if output_annotated_path else None,
        }
