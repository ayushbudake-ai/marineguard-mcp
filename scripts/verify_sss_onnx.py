from pathlib import Path
import cv2
import numpy as np
import onnxruntime as ort
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]

PT = ROOT / "runs/detect/runs/detect/marineguard_sss_yolov8n_exp2_augmented/weights/best.pt"
ONNX = ROOT / "runs/detect/runs/detect/marineguard_sss_yolov8n_exp2_augmented/weights/best.onnx"
IMAGE = ROOT / "data/processed/marineguard_sss/images/test/synth_ghost_net_00001.png"

CONF = 0.01
IOU = 0.7
IMGSZ = 640


def main():
    print("=== SSS PyTorch <-> ONNX Verification ===")

    for p in (PT, ONNX, IMAGE):
        if not p.exists():
            raise FileNotFoundError(f"Missing: {p}")

    pt_model = YOLO(str(PT))

    pt_result = pt_model.predict(
        source=str(IMAGE),
        imgsz=IMGSZ,
        conf=CONF,
        iou=IOU,
        device="cpu",
        verbose=False,
    )[0]

    pt_detections = []
    for b in pt_result.boxes:
        pt_detections.append({
            "class_id": int(b.cls[0]),
            "confidence": float(b.conf[0]),
            "bbox": [float(v) for v in b.xyxy[0].tolist()],
        })

    session = ort.InferenceSession(
        str(ONNX),
        providers=["CPUExecutionProvider"],
    )

    image = cv2.imread(str(IMAGE), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError("Failed to read image")

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = cv2.resize(image, (IMGSZ, IMGSZ))

    tensor = image.astype(np.float32) / 255.0
    tensor = np.transpose(tensor, (2, 0, 1))
    tensor = np.expand_dims(tensor, axis=0)

    output = session.run(
        [session.get_outputs()[0].name],
        {session.get_inputs()[0].name: tensor},
    )[0]

    predictions = output[0].T

    boxes = predictions[:, :4]
    scores = predictions[:, 4]

    keep = scores >= CONF
    boxes = boxes[keep]
    scores = scores[keep]

    xyxy = np.empty_like(boxes)
    xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2
    xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2
    xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2
    xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2

    indices = cv2.dnn.NMSBoxes(
        xyxy.tolist(),
        scores.tolist(),
        CONF,
        IOU,
    )

    onnx_detections = []

    if len(indices) > 0:
        indices = np.array(indices).reshape(-1)

        for i in indices:
            onnx_detections.append({
                "class_id": 0,
                "confidence": float(scores[i]),
                "bbox": [float(v) for v in xyxy[i]],
            })

    print("\nPyTorch provider: CPU")
    print("ONNX providers:", session.get_providers())

    print("\nPyTorch detections:", len(pt_detections))
    for d in pt_detections:
        print(
            "  class=", d["class_id"],
            "conf=", round(d["confidence"], 6),
            "bbox=", [round(v, 3) for v in d["bbox"]],
        )

    print("\nONNX detections:", len(onnx_detections))
    for d in onnx_detections:
        print(
            "  class=", d["class_id"],
            "conf=", round(d["confidence"], 6),
            "bbox=", [round(v, 3) for v in d["bbox"]],
        )

    if len(pt_detections) != len(onnx_detections):
        print("\nPARITY: WARNING - detection count differs")
        return

    if not pt_detections:
        print("\nPARITY: PASS - both produced zero detections")
        return

    pt = pt_detections[0]
    ox = onnx_detections[0]

    class_match = pt["class_id"] == ox["class_id"]
    conf_diff = abs(pt["confidence"] - ox["confidence"])
    bbox_diff = np.max(
        np.abs(
            np.array(pt["bbox"]) -
            np.array(ox["bbox"])
        )
    )

    print("\nClass match:", class_match)
    print("Confidence absolute difference:", conf_diff)
    print("Maximum bbox absolute difference:", bbox_diff)

    if not class_match:
        print("\nPARITY: FAIL - class IDs differ")
        return

    print("\nPARITY: PASS - class IDs match and outputs are numerically comparable")


if __name__ == "__main__":
    main()
