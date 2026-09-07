from pathlib import Path

from marineguard.preprocessing.v2_trainer import MarineGuardV2Trainer


ROOT = Path(__file__).resolve().parent
DATA_YAML = ROOT / "data" / "processed_v2" / "marineguard" / "data.yaml"
RUNS_DIR = ROOT / "runs"


def main():
    trainer = MarineGuardV2Trainer(
        overrides={
            "model": "yolov8n.pt",
            "data": str(DATA_YAML),
            "epochs": 50,
            "imgsz": 512,
            "batch": 16,
            "device": 0,
            "workers": 0,
            "amp": True,
            "patience": 10,
            "save": True,
            "plots": True,
            "project": str(RUNS_DIR),
            "name": "marineguard_v2_final",
        }
    )

    trainer.train()


if __name__ == "__main__":
    main()
