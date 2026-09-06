from ultralytics import YOLO

def main():
    model = YOLO(
        r"C:\aaaa\SIH\marineguard-mcp\runs\marineguard_full_512_b16-2\weights\best.pt"
    )

    results = model.val(
        data=r"C:\aaaa\SIH\marineguard-mcp\data\processed\marineguard\data.yaml",
        split="test",
        imgsz=512,
        batch=16,
        device=0,
        workers=0,
        plots=True,
        project=r"C:\aaaa\SIH\marineguard-mcp\runs",
        name="marineguard_test_evaluation",
    )

    print("\nTEST EVALUATION COMPLETE")
    print(f"Precision: {results.box.mp}")
    print(f"Recall:    {results.box.mr}")
    print(f"mAP50:     {results.box.map50}")
    print(f"mAP50-95:  {results.box.map}")

if __name__ == "__main__":
    main()