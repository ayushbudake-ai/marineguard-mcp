from ultralytics import YOLO


def main():
    model = YOLO("yolov8n.pt")

    model.train(
        data=r"C:\aaaa\SIH\marineguard-mcp\data\processed\marineguard\data.yaml",
        epochs=50,
        imgsz=512,
        batch=16,
        device=0,
        workers=0,
        amp=True,
        patience=10,
        save=True,
        plots=True,
        project=r"C:\aaaa\SIH\marineguard-mcp\runs",
        name="marineguard_full_512_b16",
    )


if __name__ == "__main__":
    main()