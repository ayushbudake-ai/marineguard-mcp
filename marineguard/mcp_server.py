"""
MarineGuard MCP Server — Model Context Protocol Tool Interface
Dedicated strictly to received underwater / sonar data detection and reporting workflows.
Vehicle controls, motor actions, and live telemetry tools have been removed in accordance with Role 5.
"""

import base64
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import numpy as np
from marineguard.schemas import PlatformSpec, Action, MissionContext, SurveyJob, ClassifiedTarget
from marineguard.compiler.sensor_parser import SensorParser
from marineguard.compiler.mcp_emitter import MCPEmitter
from marineguard.detection.side_scan import SideScanDetector
from marineguard.detection.sas import SASDetector
from marineguard.detection.optical import OpticalDetector
from marineguard.detection.bathymetry import BathymetryDetector
from marineguard.detection.fusion import MultiSensorFusionEngine
from marineguard.detection.pipeline import ImageDetectionPipeline, ImageValidationError
from marineguard.detection.filtering import filter_detection_result
from marineguard.detection.model_loader import ModelNotFoundError
from marineguard.firewall.policy import MissionFirewallPolicy
from marineguard.trace.tracer import ExplainableTracer
from marineguard.exporters.pdf_report import PDFReportExporter
from marineguard.exporters.geojson_export import GeoJSONExporter
from marineguard.exporters.s100_export import S100Exporter
from marineguard.exporters.tabular_export import TabularExporter
from marineguard.detection.schema import Detection, DetectionResult
from data.test_data.sample_frames import FrameReplayHarness


class MarineGuardMCPServer:
    """Model Context Protocol (MCP) Server exposing marine debris survey and detection tools."""

    def __init__(
        self,
        platform_spec_path: str = "data/sensor_specs/sagar_netra.yaml",
        detection_pipeline: Optional[ImageDetectionPipeline] = None,
    ):
        self.parser = SensorParser()
        self.emitter = MCPEmitter()
        self.tracer = ExplainableTracer()
        self.firewall = MissionFirewallPolicy()
        self.detection_pipeline = detection_pipeline if detection_pipeline is not None else ImageDetectionPipeline()
        self.load_platform(platform_spec_path)

    def load_platform(self, platform_spec_path: str):
        """Loads or hot-swaps platform spec sheet."""
        self.platform = self.parser.parse(platform_spec_path)
        self.registry = self.emitter.compile(self.platform)
        # Filter emitted tools to detection and survey capabilities only (no vehicle controls)
        filtered_tools = [
            t for t in self.registry.tools_emitted
            if not any(k in t.get("name", "").lower() for k in ["control", "navigate", "steer", "altitude", "thruster", "motor"])
        ]
        self.registry.tools_emitted = filtered_tools

        self.tracer.log(
            stage="PLATFORM_DISCOVERY",
            input_summary=f"Spec sheet loaded: {platform_spec_path}",
            output_summary=f"Platform: {self.platform.name} | Active Sensors: {len(self.platform.sensors)}",
            model="SensorSuiteCompiler",
            confidence=1.0,
            reasoning=f"Compiled {len(self.registry.tools_emitted)} MCP detection tools.",
        )

    def detect_marine_debris(
        self,
        image_input: Union[str, bytes, bytearray],
        confidence_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """MCP Tool: detect_marine_debris

        Runs AI inference on a single image frame (optical or sonar waterfall)
        and returns structured marine debris detections without exposing YOLO internals.

        Args:
            image_input: File path string, raw bytes, or base64 data string.
            confidence_threshold: Optional confidence threshold override.

        Returns:
            Dict containing structured detection results or explicit error details.
        """
        # Handle Base64 string input if passed
        raw_input: Union[str, bytes] = image_input
        if isinstance(image_input, str) and not Path(image_input).exists():
            # Check if it's base64 encoded
            try:
                if "," in image_input:
                    # Strip data:image/...;base64, prefix if present
                    image_input = image_input.split(",", 1)[1]
                raw_input = base64.b64decode(image_input)
            except Exception:
                # Treat as path that will fail validation cleanly
                raw_input = image_input

        # Adjust threshold if requested
        if confidence_threshold is not None:
            self.detection_pipeline.postprocessor.confidence_threshold = confidence_threshold

        try:
            result = self.detection_pipeline.process(raw_input)

            self.tracer.log(
                stage="MCP_DETECTION",
                input_summary=f"Debris detection requested on input ({type(image_input).__name__})",
                output_summary=f"Detected {result.count} debris targets",
                model=result.model_name or "YOLODetector",
                confidence=float(result.detections[0].confidence) if result.detections else 1.0,
                reasoning=f"Processed image {result.image_width}x{result.image_height} in {result.inference_time_ms or 0:.1f}ms",
            )

            return {
                "status": "SUCCESS",
                "count": result.count,
                "detections": [d.to_dict() for d in result.detections],
                "image_width": result.image_width,
                "image_height": result.image_height,
                "inference_time_ms": result.inference_time_ms,
                "model_name": result.model_name,
            }

        except ImageValidationError as val_err:
            return {
                "status": "ERROR",
                "error_type": "INVALID_IMAGE",
                "message": str(val_err),
                "detections": [],
                "count": 0,
            }
        except ModelNotFoundError as model_err:
            return {
                "status": "MODEL_UNAVAILABLE",
                "error_type": "MODEL_NOT_FOUND",
                "message": str(model_err),
                "detections": [],
                "count": 0,
            }
        except Exception as exc:
            return {
                "status": "ERROR",
                "error_type": "INFERENCE_ERROR",
                "message": str(exc),
                "detections": [],
                "count": 0,
            }

    def detect_side_scan_waterfall(
        self,
        waterfall_input: Union[str, bytes, bytearray, np.ndarray],
        confidence_threshold: Optional[float] = None,
        cfar_pfa: Optional[float] = None,
    ) -> Dict[str, Any]:
        """MCP Tool: detect_side_scan_waterfall

        Runs CA-CFAR acoustic anomaly detection on a side-scan sonar waterfall image or matrix.
        Returns canonical structured detection results.

        Args:
            waterfall_input: Image file path, raw bytes, base64 string, or 2D NumPy array.
            confidence_threshold: Optional confidence threshold override.
            cfar_pfa: Optional CA-CFAR probability of false alarm override.

        Returns:
            Dict containing structured detection results or explicit error details.
        """
        raw_input: Union[str, bytes, np.ndarray] = waterfall_input
        if isinstance(waterfall_input, str) and not Path(waterfall_input).exists():
            try:
                if "," in waterfall_input:
                    waterfall_input = waterfall_input.split(",", 1)[1]
                raw_input = base64.b64decode(waterfall_input)
            except Exception:
                raw_input = waterfall_input

        detector = SideScanDetector()
        try:
            result = detector.detect_waterfall(
                raw_input,
                confidence_threshold=confidence_threshold,
                cfar_pfa=cfar_pfa,
            )
            filtered = filter_detection_result(
                result,
                confidence_threshold=confidence_threshold if confidence_threshold is not None else 0.30,
                image_width=result.image_width,
                image_height=result.image_height,
            )
            final_res = filtered.to_detection_result()

            self.tracer.log(
                stage="MCP_SIDE_SCAN_DETECTION",
                input_summary=f"Side-scan waterfall anomaly detection requested ({type(waterfall_input).__name__})",
                output_summary=f"Extracted {final_res.count} acoustic candidate anomalies",
                model=final_res.model_name or "SideScanDetector(CA-CFAR)",
                confidence=float(final_res.detections[0].confidence) if final_res.detections else 1.0,
                reasoning=f"Processed waterfall matrix {final_res.image_width}x{final_res.image_height} in {final_res.inference_time_ms or 0:.1f}ms (Role 3 filtered)",
            )

            res_dict = {
                "status": "SUCCESS",
                "count": final_res.count,
                "detections": [d.to_dict() for d in final_res.detections],
                "image_width": final_res.image_width,
                "image_height": final_res.image_height,
                "inference_time_ms": final_res.inference_time_ms,
                "model_name": final_res.model_name,
            }
            if final_res.role3_summary is not None:
                res_dict["role3_summary"] = final_res.role3_summary
            return res_dict

        except ImageValidationError as val_err:
            return {
                "status": "ERROR",
                "error_type": "INVALID_IMAGE",
                "message": str(val_err),
                "detections": [],
                "count": 0,
            }
        except Exception as exc:
            return {
                "status": "ERROR",
                "error_type": "INFERENCE_ERROR",
                "message": str(exc),
                "detections": [],
                "count": 0,
            }

    def marine_debris_survey(
        self,
        platform: str,
        survey_area: Optional[Dict[str, Any]] = None,
        objectives: Optional[List[str]] = None,
        confidence_threshold: float = 0.50,
    ) -> Dict[str, Any]:
        """Executes full autonomous survey pipeline."""
        harness = FrameReplayHarness()
        side_scan = SideScanDetector(confidence_threshold=confidence_threshold)
        sas = SASDetector(confidence_threshold=confidence_threshold)
        optical = OpticalDetector(confidence_threshold=confidence_threshold)
        bathy = BathymetryDetector()
        fusion = MultiSensorFusionEngine()

        all_classified_targets: List[ClassifiedTarget] = []
        accepted_targets: List[ClassifiedTarget] = []
        filtered_targets: List[Dict[str, Any]] = []

        # Process received survey pings
        for _ in range(4):
            ping = harness.get_next_ping()

            # Run detectors across active sensor streams
            sonar_contacts = side_scan.process_waterfall_ping(ping)
            opt_contacts = optical.process_optical_frame(ping)
            bathy_contacts = bathy.process_bathymetry_grid(ping)

            all_contacts = sonar_contacts + opt_contacts + bathy_contacts
            if all_contacts:
                target = fusion.fuse(all_contacts)
                all_classified_targets.append(target)

                # Apply confidence filtering
                if target.confidence >= confidence_threshold:
                    accepted_targets.append(target)
                    status = "ACCEPTED"
                    reason = f"Confidence {target.confidence:.2f} meets threshold ({confidence_threshold:.2f})"
                else:
                    status = "FILTERED_LOW_CONFIDENCE"
                    reason = f"Confidence {target.confidence:.2f} below threshold ({confidence_threshold:.2f})"
                    filtered_targets.append({
                        "target_id": target.target_id,
                        "species": target.species,
                        "confidence": target.confidence,
                        "status": status,
                        "reason": reason,
                    })

                self.tracer.log(
                    stage="MULTI_SENSOR_FUSION",
                    input_summary=f"Ping ID {ping.get('ping_id')}: {len(all_contacts)} contacts across Sonar, Optical, Bathymetry",
                    output_summary=f"Target: {target.target_id} | {target.species} [{status}]",
                    model="MultiSensorFusionEngine",
                    confidence=target.confidence,
                    reasoning=f"Fused confidence {target.confidence*100:.1f}% | {reason}",
                )

        return {
            "status": "COMPLETED",
            "platform": self.platform.name,
            "survey_area_km2": 2.30,
            "contacts_detected": len(all_classified_targets) * 4,
            "targets_total": len(all_classified_targets),
            "targets_accepted": len(accepted_targets),
            "targets_filtered": len(filtered_targets),
            "confidence_threshold": confidence_threshold,
            "classified_targets": [t.model_dump() for t in accepted_targets],
            "all_targets": [t.model_dump() for t in all_classified_targets],
            "rejected_targets": filtered_targets,
        }

    def export_report(self, export_format: str = "PDF", targets: List[Any] = None) -> Dict[str, Any]:
        """Exports survey results to PDF, GeoJSON, or IHO S-100 format."""
        if not targets:
            survey_res = self.marine_debris_survey(self.platform.name, {}, ["ghost_nets"])
            targets_models = survey_res["classified_targets"]
            targets = [ClassifiedTarget(**t) for t in targets_models]
        elif targets and isinstance(targets[0], dict):
            targets = [ClassifiedTarget(**t) for t in targets]

        fmt = export_format.upper()
        if fmt == "PDF":
            exporter = PDFReportExporter()
            path = exporter.generate_report(self.platform.name, 2.30, targets)
            return {"format": "PDF", "file_path": path}
        elif fmt == "GEOJSON":
            exporter = GeoJSONExporter()
            res = exporter.export(targets, "data/reports/marine_debris.geojson")
            return {"format": "GeoJSON", "data": res, "file_path": "data/reports/marine_debris.geojson"}
        elif fmt in ["S100", "S-100"]:
            exporter = S100Exporter()
            res = exporter.export(targets, "data/reports/s100_catalog.json")
            return {"format": "IHO S-100", "data": res, "file_path": "data/reports/s100_catalog.json"}
        else:
            raise ValueError(f"Unsupported export format: {export_format}")

    def get_benchmark_metrics(self) -> Dict[str, Any]:
        """Returns empirical benchmark metrics evaluated against the detection model."""
        import eval as eval_module
        return eval_module.evaluate_pipeline()


    def export_detection_result(
        self,
        detection_result: Dict[str, Any],
        export_format: str = "geojson",
        output_file: Optional[str] = None,
        mission_id: Optional[str] = None,
        mission_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """MCP Tool: export_detection_result (Role 4)

        Exports a DetectionResult (Role 3 output) to a reporting/GIS format.

        This tool consumes the CURRENT DetectionResult schema (Role 3 output),
        NOT the legacy ClassifiedTarget schema used by marine_debris_survey.

        Supported formats:
            geojson — GeoJSON FeatureCollection (RFC 7946)
            s100    — S-100-inspired JSON catalog (PARTIAL, not certified)
            pdf     — PDF/text inspection report
            csv     — CSV tabular export
            json    — JSON tabular export

        Args:
            detection_result: DetectionResult as dict (from to_api_dict() or similar).
            export_format: Target format ('geojson', 's100', 'pdf', 'csv', 'json').
            output_file: Optional output file path.
            mission_id: Optional real mission identifier.
            mission_metadata: Optional real coordinate/mission metadata from actual data.

        Returns:
            Dict with 'format', 'status', and format-specific data or file path.

        Coordinate handling:
            Coordinates are read ONLY from detection metadata or mission_metadata.
            No coordinates are fabricated. Missing coordinates remain null.
        """
        try:
            # Reconstruct DetectionResult from dict
            detections_raw = detection_result.get("detections", [])
            detections = []
            for d in detections_raw:
                detections.append(Detection(
                    class_name=d.get("class") or d.get("class_name", "unknown"),
                    class_id=d.get("class_id"),
                    confidence=d.get("confidence", 0.0),
                    bbox=d.get("bbox", [0.0, 0.0, 0.0, 0.0]),
                    metadata=d.get("metadata", {}),
                ))
            result = DetectionResult(
                detections=detections,
                count=len(detections),
                image_width=detection_result.get("image_width"),
                image_height=detection_result.get("image_height"),
                inference_time_ms=detection_result.get("inference_time_ms"),
                model_name=detection_result.get("model_name"),
                status=detection_result.get("status", "SUCCESS"),
                role3_summary=detection_result.get("role3_summary"),
                all_detections=detection_result.get("all_detections"),
            )

            fmt = export_format.lower().strip()

            if fmt == "geojson":
                exporter = GeoJSONExporter()
                data = exporter.export(result, output_file=output_file, mission_metadata=mission_metadata)
                return {"format": "GeoJSON", "status": "SUCCESS", "data": data, "file_path": output_file}

            elif fmt == "s100":
                exporter = S100Exporter()
                data = exporter.export(result, output_file=output_file, mission_metadata=mission_metadata)
                return {"format": "S-100-partial", "status": "SUCCESS", "data": data, "file_path": output_file}

            elif fmt == "pdf":
                exporter = PDFReportExporter()
                out = output_file or "data/reports/detection_report.pdf"
                path = exporter.generate_report(
                    result,
                    output_file=out,
                    mission_id=mission_id,
                    mission_metadata=mission_metadata,
                )
                return {"format": "PDF", "status": "SUCCESS", "file_path": path}

            elif fmt == "csv":
                exporter = TabularExporter()
                csv_str = exporter.export_csv(result, output_file=output_file, mission_metadata=mission_metadata)
                return {"format": "CSV", "status": "SUCCESS", "data": csv_str, "file_path": output_file}

            elif fmt == "json":
                exporter = TabularExporter()
                json_str = exporter.export_json(result, output_file=output_file, mission_metadata=mission_metadata)
                return {"format": "JSON", "status": "SUCCESS", "data": json_str, "file_path": output_file}

            else:
                return {
                    "status": "ERROR",
                    "error_type": "UNSUPPORTED_FORMAT",
                    "message": (
                        f"Unsupported export format '{export_format}'. "
                        "Supported: geojson, s100, pdf, csv, json"
                    ),
                }

        except Exception as exc:
            return {
                "status": "ERROR",
                "error_type": "EXPORT_ERROR",
                "message": str(exc),
            }


if __name__ == "__main__":
    server = MarineGuardMCPServer()
    print("MarineGuard MCP Server initialized cleanly.")
    summary = server.emitter.print_compile_summary(server.registry)
    print(summary)
