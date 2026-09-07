import io
import json
import time
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw

from marineguard.v1_detector import MarineGuardV1Detector


st.set_page_config(
    page_title="MarineGuard MCP — V1 Detection",
    page_icon="🌊",
    layout="wide",
)


st.markdown(
    """
    <style>
        .main-header {
            font-size: 2.4rem;
            font-weight: 700;
            margin-bottom: 0;
        }

        .sub-header {
            color: #64748b;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        .metric-card {
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid #334155;
            text-align: center;
        }

        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
        }

        .metric-label {
            color: #64748b;
            font-size: 0.85rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_v1_detector():
    return MarineGuardV1Detector()


try:
    detector = get_v1_detector()
except Exception as exc:
    st.error(f"Failed to load MarineGuard V1 model: {exc}")
    st.stop()


st.markdown(
    "<div class='main-header'>🌊 MarineGuard MCP</div>",
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='sub-header'>"
    "Marine Debris Detection — MarineGuard V1 / YOLOv8n"
    "</div>",
    unsafe_allow_html=True,
)


st.sidebar.header("MarineGuard V1")
st.sidebar.success("Model loaded")

st.sidebar.write(f"**Model:** {detector.model_path.name}")
st.sidebar.write("**Version:** v1")
st.sidebar.write("**Architecture:** YOLOv8n")
st.sidebar.write("**Input:** 512 × 512")
st.sidebar.write("**Classes:** 50")

confidence_threshold = st.sidebar.slider(
    "Confidence threshold",
    min_value=0.05,
    max_value=0.95,
    value=0.25,
    step=0.05,
)

input_mode = st.sidebar.radio(
    "Input mode",
    ["Single image", "Batch images"],
)


temp_dir = Path(".streamlit_tmp")
temp_dir.mkdir(exist_ok=True)


def draw_detections(image, detections):
    annotated = image.copy()
    draw = ImageDraw.Draw(annotated)

    for detection in detections:
        bbox = detection["bbox"]

        x1 = bbox["x1"]
        y1 = bbox["y1"]
        x2 = bbox["x2"]
        y2 = bbox["y2"]

        class_name = detection["class_name"]
        confidence = detection["confidence"]

        draw.rectangle(
            [x1, y1, x2, y2],
            outline="red",
            width=3,
        )

        label = f"{class_name} {confidence:.2f}"

        draw.text(
            (x1, max(0, y1 - 18)),
            label,
            fill="red",
        )

    return annotated


def run_detection(uploaded_file):
    image = Image.open(uploaded_file).convert("RGB")

    image_path = temp_dir / uploaded_file.name
    image.save(image_path)

    start = time.perf_counter()

    detection_output = detector.predict(
        image_path,
        confidence=confidence_threshold,
    )

    latency_ms = (time.perf_counter() - start) * 1000

    return image, detection_output, latency_ms


def detection_table(detections):
    rows = []

    for detection in detections:
        bbox = detection["bbox"]

        rows.append(
            {
                "Class ID": detection["class_id"],
                "Class": detection["class_name"],
                "Confidence": f"{detection['confidence'] * 100:.2f}%",
                "X1": bbox["x1"],
                "Y1": bbox["y1"],
                "X2": bbox["x2"],
                "Y2": bbox["y2"],
            }
        )

    return rows


if input_mode == "Single image":

    st.subheader("📤 Input Image")

    uploaded_file = st.file_uploader(
        "Upload a marine/sonar image",
        type=["jpg", "jpeg", "png", "bmp"],
    )

    if uploaded_file is not None:

        image, detection_output, latency_ms = run_detection(uploaded_file)

        detections = detection_output["detections"]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Input")
            st.image(image, use_container_width=True)

        annotated = draw_detections(image, detections)

        with col2:
            st.markdown("### V1 Detection")
            st.image(annotated, use_container_width=True)

        st.markdown("### Detection Summary")

        m1, m2, m3, m4 = st.columns(4)

        with m1:
            st.markdown(
                f"""
                <div class='metric-card'>
                    <div class='metric-value'>{len(detections)}</div>
                    <div class='metric-label'>Detections</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with m2:
            st.markdown(
                """
                <div class='metric-card'>
                    <div class='metric-value'>v1</div>
                    <div class='metric-label'>Model Version</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with m3:
            unique_classes = len(
                set(d["class_id"] for d in detections)
            )

            st.markdown(
                f"""
                <div class='metric-card'>
                    <div class='metric-value'>{unique_classes}</div>
                    <div class='metric-label'>Classes Found</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with m4:
            st.markdown(
                f"""
                <div class='metric-card'>
                    <div class='metric-value'>{latency_ms:.2f} ms</div>
                    <div class='metric-label'>Inference Latency</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### 🎯 Detected Objects")

        if detections:
            st.dataframe(
                detection_table(detections),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(
                "No objects detected above the selected confidence threshold."
            )

        st.markdown("### 📋 Detection Contract")

        st.caption(
            "Standardized detector output consumed by downstream roles."
        )

        st.json(detection_output)

        json_bytes = json.dumps(
            detection_output,
            indent=2,
        ).encode("utf-8")

        st.download_button(
            label="⬇️ Download Detection JSON",
            data=json_bytes,
            file_name=f"{detection_output['frame_id']}_v1_detection.json",
            mime="application/json",
        )

    else:
        st.info(
            "Upload a JPG, JPEG, PNG, or BMP image to run MarineGuard V1 detection."
        )


else:

    st.subheader("📁 Batch Marine/ Sonar Detection")

    uploaded_files = st.file_uploader(
        "Upload multiple marine/sonar images",
        type=["jpg", "jpeg", "png", "bmp"],
        accept_multiple_files=True,
    )

    if uploaded_files:

        results = []
        detection_outputs = {}

        progress = st.progress(0)

        for index, uploaded_file in enumerate(uploaded_files):

            image, detection_output, latency_ms = run_detection(
                uploaded_file
            )

            detections = detection_output["detections"]

            results.append(
                {
                    "Image": uploaded_file.name,
                    "Detections": len(detections),
                    "Classes": len(
                        set(d["class_id"] for d in detections)
                    ),
                    "Latency (ms)": round(latency_ms, 2),
                    "Max Confidence": (
                        round(
                            max(
                                d["confidence"]
                                for d in detections
                            )
                            * 100,
                            2,
                        )
                        if detections
                        else 0
                    ),
                }
            )

            detection_outputs[uploaded_file.name] = detection_output

            progress.progress(
                int((index + 1) / len(uploaded_files) * 100)
            )

        progress.empty()

        results_df = pd.DataFrame(results)

        st.markdown("### 📊 Batch Summary")

        total_images = len(results)
        total_detections = int(results_df["Detections"].sum())
        average_latency = float(
            results_df["Latency (ms)"].mean()
        )
        throughput = (
            1000 / average_latency
            if average_latency > 0
            else 0
        )

        m1, m2, m3, m4 = st.columns(4)

        with m1:
            st.metric("Images", total_images)

        with m2:
            st.metric("Total Detections", total_detections)

        with m3:
            st.metric(
                "Average Latency",
                f"{average_latency:.2f} ms",
            )

        with m4:
            st.metric(
                "Throughput",
                f"{throughput:.2f} images/sec",
            )

        st.markdown("### 📋 Per-Image Results")

        st.dataframe(
            results_df,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### 🎯 Detection Results")

        for filename, output in detection_outputs.items():

            detections = output["detections"]

            with st.expander(
                f"{filename} — {len(detections)} detections"
            ):

                uploaded_match = next(
                    file
                    for file in uploaded_files
                    if file.name == filename
                )

                image = Image.open(uploaded_match).convert("RGB")
                annotated = draw_detections(image, detections)

                c1, c2 = st.columns(2)

                with c1:
                    st.image(
                        image,
                        caption="Input",
                        use_container_width=True,
                    )

                with c2:
                    st.image(
                        annotated,
                        caption="V1 Detection",
                        use_container_width=True,
                    )

                if detections:
                    st.dataframe(
                        detection_table(detections),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No detections.")

                st.json(output)

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(
            zip_buffer,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as zip_file:

            for filename, output in detection_outputs.items():

                json_name = (
                    Path(filename).stem
                    + "_v1_detection.json"
                )

                zip_file.writestr(
                    json_name,
                    json.dumps(
                        output,
                        indent=2,
                    ),
                )

        st.download_button(
            label="⬇️ Download All Detection JSON",
            data=zip_buffer.getvalue(),
            file_name="marineguard_v1_detection_results.zip",
            mime="application/zip",
        )

    else:
        st.info(
            "Upload multiple JPG, JPEG, PNG, or BMP images to run batch detection."
        )


st.markdown("---")

st.caption(
    "MarineGuard V1 • YOLOv8n • 50 classes • Standard Detection Contract"
)
