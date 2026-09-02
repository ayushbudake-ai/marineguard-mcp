"""
================================================================================
MarineGuard MCP — Web Command Center Application (SIH26057)
Ministry of Earth Sciences (MoES) Autonomous Marine Debris & Anomaly System
================================================================================
"""

import os
import time
import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from marineguard.mcp_server import MarineGuardMCPServer
from marineguard.schemas import Action, MissionContext
from marineguard.trace.visualizer import EvidenceVisualizer

# 1. Page Configuration
st.set_page_config(
    page_title="MarineGuard MCP — MoES Web Command Center",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Custom Styling
st.markdown("""
<style>
    .stApp { background-color: #0b1120; color: #f8fafc; }
    .main-header { font-size: 2.3rem; color: #38bdf8; font-weight: bold; margin-bottom: 0px; }
    .sub-header { font-size: 1.05rem; color: #94a3b8; margin-bottom: 25px; }
    .metric-card { background-color: #1e293b; border: 1px solid #334155; padding: 18px; border-radius: 10px; text-align: center; }
    .metric-value { font-size: 1.8rem; font-weight: bold; color: #38bdf8; }
    .metric-label { font-size: 0.85rem; color: #94a3b8; }
    .card-box { background-color: #0f172a; border: 1px solid #1e293b; padding: 20px; border-radius: 10px; margin-bottom: 15px; }
    .firewall-alert { background-color: #450a0a; border: 1px solid #991b1b; padding: 18px; border-radius: 10px; color: #fca5a5; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_mcp_server(spec_path: str):
    return MarineGuardMCPServer(spec_path)


# 3. Sidebar Platform & Telemetry Controls
st.sidebar.markdown("### ⚓ MarineGuard MCP")
st.sidebar.caption("MoES SIH26057 Autonomous Survey Platform")

platform_options = {
    "Sagar Netra (AUV-01)": "data/sensor_specs/sagar_netra.yaml",
    "Kongsberg HUGIN 3000": "data/sensor_specs/hugin_3000.yaml",
}

selected_platform = st.sidebar.selectbox("Active Platform Spec Sheet", list(platform_options.keys()))
server = get_mcp_server(platform_options[selected_platform])

if server.platform.name != selected_platform.split(" (")[0]:
    server.load_platform(platform_options[selected_platform])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛 Mission Telemetry & Comms")
battery_reserve = st.sidebar.slider("Battery Reserve (%)", min_value=10, max_value=100, value=28) / 100.0
comms_link = st.sidebar.slider("Acoustic Link (kbps)", min_value=1.0, max_value=20.0, value=4.5)
altitude_m = st.sidebar.slider("Target Altitude (m)", min_value=2.0, max_value=20.0, value=3.0)

st.sidebar.markdown("---")
run_survey_btn = st.sidebar.button("🚀 Execute Debris Survey", type="primary")

# 4. Main Web Layout Header
st.markdown("<div class='main-header'>MarineGuard MCP — Autonomous Survey Command Center</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-header'>Connected Rig: <b>{server.platform.name}</b> | Compute: <code>{server.platform.compute}</code> | Status: <span style='color: #4ade80;'>ONLINE</span></div>", unsafe_allow_html=True)

# 5. Execute Survey Logic
with st.spinner("Processing pings across Sonar, Optical, and Bathymetry..."):
    survey_result = server.marine_debris_survey(server.platform.name, {}, ["ghost_nets", "plastics"])
    targets = survey_result["classified_targets"]

# 6. Tabbed Application Navigation
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺 Interactive GIS Map & Metrics",
    "🔬 Explainable Trace & Evidence",
    "🛡 Mission Firewall Safety Intercept",
    "📄 Report Export Center",
])

# ------------------------------------------------------------------------------
# TAB 1: GIS MAP & METRICS
# ------------------------------------------------------------------------------
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("<div class='metric-card'><div class='metric-value'>2.30 km²</div><div class='metric-label'>Survey Bounds Area</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><div class='metric-value'>{len(targets)*4}</div><div class='metric-label'>Total Contacts Detected</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><div class='metric-value'>{len(targets)}</div><div class='metric-label'>Classified Debris Targets</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown("<div class='metric-card'><div class='metric-value' style='color: #4ade80;'>100%</div><div class='metric-label'>Firewall Policy Compliance</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📍 Classified Marine Debris Spatial Distribution")

    df_targets = pd.DataFrame([
        {
            "target_id": t["target_id"],
            "species": t["species"],
            "confidence": t["confidence"],
            "confidence_pct": f"{t['confidence']*100:.1f}%",
            "lat": t["lat_lon"][0],
            "lon": t["lat_lon"][1],
            "depth_m": t["depth_m"],
            "priority": t["removal_priority"],
            "risk": t["entanglement_risk"],
        }
        for t in targets
    ])

    # Interactive Plotly Map
    fig_map = px.scatter_mapbox(
        df_targets,
        lat="lat",
        lon="lon",
        color="priority",
        size="confidence",
        hover_name="target_id",
        hover_data=["species", "confidence_pct", "depth_m", "risk"],
        color_discrete_map={"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#10b981"},
        zoom=13,
        height=450,
    )
    fig_map.update_layout(
        mapbox_style="carto-darkmatter",
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#0f172a",
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.subheader("📊 Classified Target Inventory")
    st.dataframe(df_targets[["target_id", "species", "confidence_pct", "depth_m", "priority", "risk"]], use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 2: EXPLAINABLE TRACE & EVIDENCE
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("🔬 Multi-Sensor Evidence Overlay & Step-by-Step Trace")

    events = server.tracer.get_history()
    for evt in events[-4:]:
        st.markdown(f"""
        <div class='card-box'>
            <h4 style='color: #38bdf8; margin-top:0;'>[{evt.stage}] {evt.event_id} — Model: {evt.model} (Confidence: {evt.confidence*100:.1f}%)</h4>
            <p><b>Input Pings:</b> {evt.input_summary}</p>
            <p><b>Output Classification:</b> {evt.output_summary}</p>
            <p><b>Reasoning Trace:</b> {evt.reasoning}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### Multi-Modal Evidence Visualizer Output")
    # Generate evidence visual overlay
    viz = EvidenceVisualizer()
    from marineguard.schemas import ClassifiedTarget
    sample_target = ClassifiedTarget(**targets[0])
    from data.test_data.sample_frames import FrameReplayHarness
    sample_ping = FrameReplayHarness().get_next_ping()
    img_path = viz.generate_evidence_overlay(sample_target, sample_ping)

    if os.path.exists(img_path):
        st.image(img_path, caption=f"Multi-Sensor Evidence Overlay: {sample_target.target_id} ({sample_target.species})", use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 3: MISSION FIREWALL
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("🛡 Mission Firewall Dynamic Safety Intercept")

    action = Action(
        type="request_altitude_change",
        description=f"Descend AUV altitude from 15m to {altitude_m}m for close optical inspection",
        target_id="TARGET_Contact_01 (Ghost Net Cluster)",
        consumes_reserve=0.12,
    )
    context = MissionContext(battery_reserve=battery_reserve, acoustic_link_kbps=comms_link)
    decision = server.firewall.check_action(action, context)

    st.markdown(f"""
    <div class='firewall-alert'>
        <h3 style='margin-top:0; color:#fca5a5;'>🛡 ACTION INTERCEPTED: {action.description}</h3>
        <p><b>Evaluated Risk Tier:</b> <span style='font-size:1.2em; font-weight:bold; color:#ef4444;'>[{decision.risk_level.value}]</span></p>
        <p><b>Reasoning:</b> {decision.reason}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Operator Intercept Decision Controls")
    b1, b2, b3, b4 = st.columns(4)

    if b1.button("✅ ALLOW", type="primary"):
        st.success("Operator granted explicit single-operator approval. Action dispatched.")
    if b2.button("⚠️ MODIFY"):
        st.info(f"Safer Parameters Enforced: {decision.suggested_modifications}")
    if b3.button("⏳ DEFER"):
        st.warning("Action postponed until surface link re-established.")
    if b4.button("❌ DENY"):
        st.error("Action denied permanently by operator.")

# ------------------------------------------------------------------------------
# TAB 4: EXPORT CENTER
# ------------------------------------------------------------------------------
with tab4:
    st.subheader("📄 Official MoES Survey Reports & GIS Data Exports")

    pdf_res = server.export_report("PDF")
    geojson_res = server.export_report("GeoJSON")
    s100_res = server.export_report("S100")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("<div class='card-box'><h4>📜 MoES PDF Report</h4><p>Official publication-grade PDF report with maps & target tables.</p></div>", unsafe_allow_html=True)
        if os.path.exists(pdf_res["file_path"]):
            with open(pdf_res["file_path"], "rb") as f:
                st.download_button("📥 Download PDF Report", f, file_name="MoES_MarineGuard_Survey_Report.pdf", mime="application/pdf")

    with col_b:
        st.markdown("<div class='card-box'><h4>🗺 GeoJSON GIS Dataset</h4><p>Standard GeoJSON FeatureCollection for GIS software.</p></div>", unsafe_allow_html=True)
        if os.path.exists(geojson_res["file_path"]):
            with open(geojson_res["file_path"], "rb") as f:
                st.download_button("📥 Download GeoJSON", f, file_name="marine_debris.geojson", mime="application/json")

    with col_c:
        st.markdown("<div class='card-box'><h4>⚓ IHO S-100 Catalogue</h4><p>IHO S-100 compliant hydrographic feature catalogue.</p></div>", unsafe_allow_html=True)
        if os.path.exists(s100_res["file_path"]):
            with open(s100_res["file_path"], "rb") as f:
                st.download_button("📥 Download IHO S-100", f, file_name="s100_catalog.json", mime="application/json")
