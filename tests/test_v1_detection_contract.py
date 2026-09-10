import json
from pathlib import Path

from jsonschema import validate

from marineguard.v1_detector import MarineGuardV1Detector


def test_v1_detection_contract():
    schema = json.loads(
        Path("docs/DETECTION_SCHEMA.json").read_text(encoding="utf-8-sig")
    )

    test_images = list(Path("data/processed/marineguard/images/test").glob("*"))
    if not test_images:
        test_images = list(Path("data/processed/fls/images/test").glob("*.png")) or list(Path("data/processed/seaclear_segmentation/images/test").glob("*.jpg"))
    test_image = test_images[0]

    detector = MarineGuardV1Detector()
    output = detector.predict(test_image, confidence=0.25)

    validate(instance=output, schema=schema)

    assert output["model_version"] == "v1"
    assert isinstance(output["frame_id"], str)
    assert isinstance(output["detections"], list)

    for detection in output["detections"]:
        assert 0 <= detection["class_id"] <= 49
        assert 0 <= detection["confidence"] <= 1

        bbox = detection["bbox"]
        assert bbox["x1"] < bbox["x2"]
        assert bbox["y1"] < bbox["y2"]
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate


def test_invalid_detection_contract_is_rejected():
    schema = json.loads(
        Path("docs/DETECTION_SCHEMA.json").read_text(encoding="utf-8-sig")
    )

    invalid_output = {
        "frame_id": "test_frame",
        "model_version": "v1",
        "detections": [
            {
                "class_id": 999,
                "class_name": "invalid",
                "confidence": 1.5,
                "bbox": {
                    "x1": 100,
                    "y1": 100,
                    "x2": 50,
                    "y2": 50
                }
            }
        ]
    }

    with pytest.raises(ValidationError):
        validate(instance=invalid_output, schema=schema)
