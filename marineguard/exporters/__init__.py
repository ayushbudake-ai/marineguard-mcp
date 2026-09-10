"""
MarineGuard MCP — Role 4 Exporters Package

Exports DetectionResult (Role 3 output) to multiple formats:
    GeoJSON       — standard GIS FeatureCollection (RFC 7946)
    S-100         — partial S-100-inspired JSON catalog (NOT certified)
    PDF           — professional detection/inspection report
    CSV/JSON      — structured tabular data
    Geotagging    — coordinate extraction from real metadata

Usage:
    from marineguard.exporters.geojson_export import GeoJSONExporter
    from marineguard.exporters.s100_export import S100Exporter
    from marineguard.exporters.pdf_report import PDFReportExporter
    from marineguard.exporters.tabular_export import TabularExporter
    from marineguard.exporters.geotagging import Geotagger
"""
