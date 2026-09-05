from ultralytics import YOLO


def main():
    model = YOLO("yolov8n.pt")

    model.train(
        data=r"C:\aaaa\SIH\marineguard-mcp\data\processed\marineguard\data.yaml",
        epochs=3,
        imgsz=640,
        batch=8,
        device=0,
        workers=0,
        project=r"C:\aaaa\SIH\marineguard-mcp\runs",
        name="marineguard_sanity",
    )


if __name__ == "__main__":
    main()