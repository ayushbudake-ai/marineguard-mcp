import { useEffect, useState } from "react";
import "leaflet/dist/leaflet.css";
import { MOCK_DETECTIONS } from "../data/Mockdetection";

// TODO: replace MOCK_DETECTIONS with a fetch to the real geotagging output
// once the backend exists (see src/api/marineguard.js). Prefer consuming
// the agreed GeoJSON FeatureCollection format if that's the team's
// interchange format, and adapt the marker mapping below accordingly.

const statusColor = {
  accepted: "#3FB8AF",
  filtered: "#7C96A0",
  confirmed: "#3FB8AF",
  review: "#F4B860",
};

export default function DetectionMap() {
  const [detections] = useState(MOCK_DETECTIONS);
  const [leafletComponents, setLeafletComponents] = useState(null);
  const center = [15.372, 73.819]; // Goa coastal transect — placeholder survey area

  useEffect(() => {
    import("react-leaflet").then(({ MapContainer, TileLayer, CircleMarker, Popup }) => {
      setLeafletComponents({ MapContainer, TileLayer, CircleMarker, Popup });
    });
  }, []);

  const mapContent = leafletComponents ? (
    <leafletComponents.MapContainer
      center={center}
      zoom={13}
      scrollWheelZoom
      style={{ height: "100%", width: "100%", background: "#0A1418" }}
    >
      <leafletComponents.TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {detections.map((d) => (
        <leafletComponents.CircleMarker
          key={d.id}
          center={[d.location.latitude, d.location.longitude]}
          radius={7}
          pathOptions={{
            color: statusColor[d.status.toLowerCase()] ?? "#7C96A0",
            fillColor: statusColor[d.status.toLowerCase()] ?? "#7C96A0",
            fillOpacity: 0.85,
            weight: 2,
          }}
        >
          <leafletComponents.Popup>
            <div style={{ fontFamily: "monospace", fontSize: 12 }}>
              <div>{d.id}</div>
              <div>{d.objectClass || d.type || "Marine Debris"}</div>
              <div>
                confidence{" "}
                {typeof d.confidence === "number"
                  ? (d.confidence > 1 ? d.confidence / 100 : d.confidence).toFixed(2)
                  : "N/A"}
              </div>
              <div>{new Date(d.timestamp).toLocaleString()}</div>
            </div>
          </leafletComponents.Popup>
        </leafletComponents.CircleMarker>
      ))}
    </leafletComponents.MapContainer>
  ) : (
    <div className="flex h-full items-center justify-center text-sm text-muted">Loading map...</div>
  );

  return (
    <div>
      <h1 className="text-xl text-fg">Detection Map</h1>
      <p className="mt-1 text-sm text-muted">
        Geotagged detections from the most recent survey. Click a marker to inspect it.
      </p>

      <div className="mt-6 h-[560px] border border-line">
        {mapContent}
      </div>

      <div className="mt-4 flex gap-6 text-xs text-muted">
        <div className="flex items-center gap-2">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-teal" /> Accepted
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-muted" /> Filtered
        </div>
      </div>
    </div>
  );
}