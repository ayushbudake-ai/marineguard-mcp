from pathlib import Path

import jsonschema

from marineguard.v2_detector import MarineGuardV2Detector


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "DETECTION_SCHEMA.json"

TEST_IMAGE = (
    ROOT
    / "data"
    / "processed_v2"
    / "marineguard"
    / "images"
    / "test"
    / "v1_fls_marine-debris-aris3k-1008.png"
)


def test_v2_detection_contract():
    schema = jsonschema.validators.Draft202012Validator.check_schema(
        __import__("json").loads(
            SCHEMA_PATH.read_text(encoding="utf-8-sig")
        )
    )

    detector = MarineGuardV2Detector()

    output = detector.predict(
        TEST_IMAGE,
        confidence=0.25,
    )

    jsonschema.validate(
        instance=output,
        schema=__import__("json").loads(
            SCHEMA_PATH.read_text(encoding="utf-8-sig")
        ),
    )

    assert output["model_version"] == "v2"
    assert output["frame_id"] == TEST_IMAGE.stem
    assert isinstance(output["detections"], list)

    for detection in output["detections"]:
        assert 0 <= detection["class_id"] < 50
        assert isinstance(detection["class_name"], str)
        assert 0 <= detection["confidence"] <= 1

        bbox = detection["bbox"]

        assert isinstance(bbox["x1"], (int, float))
        assert isinstance(bbox["y1"], (int, float))
        assert isinstance(bbox["x2"], (int, float))
        assert isinstance(bbox["y2"], (int, float))


def test_invalid_v2_detection_contract_is_rejected():
    schema = __import__("json").loads(
        SCHEMA_PATH.read_text(encoding="utf-8-sig")
    )

    invalid_output = {
        "frame_id": "invalid_frame",
        "model_version": "v2",
        "detections": [
            {
                "class_id": 999,
                "class_name": "invalid",
                "confidence": 1.5,
                "bbox": {
                    "x1": 300,
                    "y1": 200,
                    "x2": 100,
                    "y2": 50,
                },
            }
        ],
    }

    try:
        jsonschema.validate(
            instance=invalid_output,
            schema=schema,
        )
    except jsonschema.ValidationError:
        return

    raise AssertionError("Invalid V2 detection contract was accepted")
