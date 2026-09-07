"""
Image Annotation Utility for MarineGuard MCP — Role 2: AI Inference & Integration

Draws bounding boxes, canonical class labels, and confidence percentages on images.
Handles zero detections, multiple detections, and overlapping boxes gracefully.
"""

from typing import Union, List, Optional, Tuple, Dict
from pathlib import Path
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from marineguard.detection.schema import Detection, DetectionResult


class ImageAnnotator:
    """Renders structured detections directly onto image frames."""

    # Distinct palette for marine debris visualization
    DEFAULT_COLORS = [
        (255, 59, 48),    # Coral Red
        (52, 199, 89),    # Sea Green
        (0, 122, 255),    # Deep Blue
        (255, 149, 0),    # Warning Orange
        (175, 82, 222),   # Purple
        (255, 204, 0),    # Yellow
        (90, 200, 250),   # Light Cyan
        (255, 45, 85),    # Pink
    ]

    def __init__(self, box_thickness: int = 2, font_size: int = 14):
        self.box_thickness = box_thickness
        self.font_size = font_size
        self._font = None
        self._load_font()

    def _load_font(self):
        """Attempts to load a clean truetype font, falls back to default bitmap font."""
        try:
            self._font = ImageFont.load_default()
        except Exception:
            self._font = None

    def _get_color_for_label(self, label: str) -> Tuple[int, int, int]:
        """Deterministic color assignment based on class label hash."""
        color_idx = abs(hash(label)) % len(self.DEFAULT_COLORS)
        return self.DEFAULT_COLORS[color_idx]

    def annotate(
        self,
        image_input: Union[str, Path, bytes, np.ndarray, Image.Image],
        detections: Union[DetectionResult, List[Detection], List[Dict]],
    ) -> Image.Image:
        """Draws bounding boxes and labels onto the given image.

        Args:
            image_input: Base image to annotate.
            detections: DetectionResult or list of Detection / dict objects.

        Returns:
            PIL.Image.Image: Annotated image.
        """
        # Load image into PIL Image
        if isinstance(image_input, (str, Path)):
            pil_img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, (bytes, bytearray)):
            pil_img = Image.open(io.BytesIO(image_input)).convert("RGB")
        elif isinstance(image_input, np.ndarray):
            pil_img = Image.fromarray(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            pil_img = image_input.copy().convert("RGB")
        else:
            raise TypeError(f"Unsupported image input type for annotator: {type(image_input)}")

        draw = ImageDraw.Draw(pil_img)
        img_w, img_h = pil_img.size

        # Normalize detection list
        det_list: List[Detection] = []
        if isinstance(detections, DetectionResult):
            det_list = detections.detections
        elif isinstance(detections, list):
            for d in detections:
                if isinstance(d, Detection):
                    det_list.append(d)
                elif isinstance(d, dict):
                    det_list.append(Detection(**d))

        for det in det_list:
            if len(det.bbox) != 4:
                continue

            x1, y1, x2, y2 = det.bbox
            x1 = max(0, min(img_w, x1))
            y1 = max(0, min(img_h, y1))
            x2 = max(0, min(img_w, x2))
            y2 = max(0, min(img_h, y2))

            if x2 <= x1 or y2 <= y1:
                continue

            color = self._get_color_for_label(det.class_name)

            # Draw segmentation polygon outline if present
            if det.segmentation and len(det.segmentation) >= 3:
                try:
                    poly_pts = [(float(pt[0]), float(pt[1])) for pt in det.segmentation if len(pt) >= 2]
                    if len(poly_pts) >= 3:
                        draw.polygon(poly_pts, outline=color)
                except Exception:
                    pass

            # Draw bounding box outline
            for i in range(self.box_thickness):
                draw.rectangle([x1 - i, y1 - i, x2 + i, y2 + i], outline=color)

            # Format label: "Class Name 91%"
            label_text = f"{det.class_name.replace('-', ' ').title()} {det.confidence * 100:.0f}%"

            # Calculate text box background
            if self._font and hasattr(draw, "textbbox"):
                bbox_text = draw.textbbox((x1, y1), label_text, font=self._font)
                text_w = bbox_text[2] - bbox_text[0]
                text_h = bbox_text[3] - bbox_text[1]
            else:
                text_w = len(label_text) * 7
                text_h = 12

            text_bg_y1 = max(0, y1 - text_h - 4)
            text_bg_y2 = y1 if y1 - text_h - 4 >= 0 else y1 + text_h + 4

            draw.rectangle([x1, text_bg_y1, x1 + text_w + 6, text_bg_y2], fill=color)
            draw.text((x1 + 3, text_bg_y1 + 2), label_text, fill=(255, 255, 255), font=self._font)

        return pil_img

    def save_annotated(
        self,
        image_input: Union[str, Path, bytes, np.ndarray, Image.Image],
        detections: Union[DetectionResult, List[Detection], List[Dict]],
        output_path: Union[str, Path],
    ) -> Path:
        """Annotates image and saves result to disk."""
        annotated_img = self.annotate(image_input, detections)
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        annotated_img.save(out_path)
        return out_path
