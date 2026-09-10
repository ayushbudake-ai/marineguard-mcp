# 🎨 Frontend & UI Layer

This folder contains the user interfaces and presentation dashboards for MarineGuard MCP.

## Components

1. **Streamlit Post-Mission Analysis Dashboard** (`streamlit_demo.py`)
   - Interactive web interface for uploading recorded sonar images (`.png`, `.jpg`, `.bmp`, `.tiff`).
   - Executes real YOLOv8 side-scan sonar detection with confidence calibration and shadow filtering.
   - Interactive GIS map visualization for geolocated survey points.
   - Direct downloads of PDF mission summaries, CSV/JSON contact logs, and GeoJSON GIS layers.
   - **Launch Command**:
     ```bash
     streamlit run streamlit_demo.py
     ```

2. **React Router v7 + Tailwind Web UI** (`my-react-router-app/` / `my-project/`)
   - Modern single-page web app with interactive bounding box canvas overlays and real-time report generation.
   - Communicates with the FastAPI backend bridge (`api_server.py`).
   - **Launch Command**:
     ```bash
     cd my-react-router-app
     npm install
     npm run dev
     ```

3. **Standalone Static Web Demos** (`docs/demo.html`, `docs/index.html`)
   - Standalone client-side demo visualizers.
