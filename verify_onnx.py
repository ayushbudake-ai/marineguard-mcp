import numpy as np
import cv2
import onnxruntime as ort
from pathlib import Path
from ultralytics import YOLO
import torch


def make_input(image_path, imgsz=512):
    image = cv2.imread(str(image_path))

    if image is None:
        raise RuntimeError(f"Could not read image: {image_path}")

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    h, w = image.shape[:2]

    scale = min(imgsz / h, imgsz / w)

    new_w = int(round(w * scale))
    new_h = int(round(h * scale))

    resized = cv2.resize(
        image,
        (new_w, new_h),
        interpolation=cv2.INTER_LINEAR,
    )

    canvas = np.full(
        (imgsz, imgsz, 3),
        114,
        dtype=np.uint8,
    )

    pad_x = (imgsz - new_w) // 2
    pad_y = (imgsz - new_h) // 2

    canvas[
        pad_y:pad_y + new_h,
        pad_x:pad_x + new_w
    ] = resized

    tensor = canvas.astype(np.float32) / 255.0

    tensor = np.transpose(
        tensor,
        (2, 0, 1),
    )

    tensor = np.expand_dims(
        tensor,
        axis=0,
    )

    return tensor


def verify():
    repo_root = Path(__file__).resolve().parent

    pt_path = (
        repo_root
        / "runs"
        / "seaclear_yolov8n_seg"
        / "train"
        / "weights"
        / "best.pt"
    )

    onnx_path = (
        repo_root
        / "runs"
        / "seaclear_yolov8n_seg"
        / "onnx"
        / "best.onnx"
    )

    val_img_dir = (
        repo_root
        / "data"
        / "processed"
        / "seaclear_segmentation"
        / "images"
        / "val"
    )

    samples = [
        val_img_dir / "1009.jpg",
        val_img_dir / "1017.jpg",
        val_img_dir / "1019.jpg",
        val_img_dir / "1037.jpg",
        val_img_dir / "1043.jpg",
    ]

    print("=== RAW PYTORCH VS ONNX SAME-TENSOR DIAGNOSTIC ===")

    print(f"PyTorch model: {pt_path}")
    print(f"ONNX model:    {onnx_path}")

    pt_model = YOLO(str(pt_path))

    session = ort.InferenceSession(
        str(onnx_path),
        providers=["CPUExecutionProvider"],
    )

    input_name = session.get_inputs()[0].name

    device = torch.device("cpu")

    pt_model.model.to(device)
    pt_model.model.eval()

    for image_path in samples:
        print(f"\n{'=' * 70}")
        print(f"IMAGE: {image_path.name}")

        tensor_np = make_input(image_path)

        tensor_pt = torch.from_numpy(tensor_np).to(device)

        with torch.no_grad():
            pt_output = pt_model.model(tensor_pt)

        onnx_outputs = session.run(
            None,
            {
                input_name: tensor_np,
            },
        )

        if isinstance(pt_output, tuple):
            pt_output0 = pt_output[0]
        else:
            pt_output0 = pt_output

        if isinstance(pt_output0, (list, tuple)):
            pt_output0 = pt_output0[0]

        if isinstance(pt_output0, torch.Tensor):
            pt_output0_np = pt_output0.detach().cpu().numpy()
        else:
            pt_output0_np = np.asarray(pt_output0)

        onnx_output0_np = np.asarray(onnx_outputs[0])

        print(f"Input shape: {tensor_np.shape}")

        print(
            f"PyTorch output shape: {pt_output0_np.shape}"
        )

        print(
            f"ONNX output shape:    {onnx_output0_np.shape}"
        )

        if pt_output0_np.shape != onnx_output0_np.shape:
            print("SHAPE MATCH: FALSE")
            continue

        abs_diff = np.abs(
            pt_output0_np - onnx_output0_np
        )

        print("SHAPE MATCH: TRUE")

        print(
            f"Max absolute difference:  {abs_diff.max():.8f}"
        )

        print(
            f"Mean absolute difference: {abs_diff.mean():.8f}"
        )

        print(
            f"PyTorch output min: {pt_output0_np.min():.8f}"
        )

        print(
            f"PyTorch output max: {pt_output0_np.max():.8f}"
        )

        print(
            f"ONNX output min:   {onnx_output0_np.min():.8f}"
        )

        print(
            f"ONNX output max:   {onnx_output0_np.max():.8f}"
        )

        pt_scores = pt_output0_np[:, 4:54, :]
        onnx_scores = onnx_output0_np[:, 4:54, :]

        pt_max_score = np.max(pt_scores)
        onnx_max_score = np.max(onnx_scores)

        print(
            f"PyTorch max class score: {pt_max_score:.8f}"
        )

        print(
            f"ONNX max class score:    {onnx_max_score:.8f}"
        )


if __name__ == "__main__":
    verify()