from ultralytics import YOLO


def main():
    model = YOLO(
        r"C:\aaaa\SIH\marineguard-mcp\runs\marineguard_full_512_b16-2\weights\last.pt"
    )

    model.train(resume=True)


if __name__ == "__main__":
    main()