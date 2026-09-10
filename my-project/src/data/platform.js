// Sourced from the README's "Supported Platforms" table. Sensor lists and
// tool counts are as stated there; nothing here is invented. The actual
// sagar_netra.yaml / hugin_3000.yaml spec files under data/sensor_specs/
// weren't available to fetch, so this stays at the granularity the README
// gives us rather than guessing at file contents.

export const PLATFORMS = [
  {
    id: "sagar_netra",
    label: "Sagar Netra (AUV-01)",
    specFile: "sagar_netra.yaml",
    toolsCompiled: 9,
    sensors: [
      { name: "Side-scan sonar", detail: "100/400 kHz" },
      { name: "MBES", detail: "Multibeam echo sounder — bathymetry" },
      { name: "Optical", detail: "4K stereo camera" },
      { name: "CTD", detail: "Conductivity / temperature / depth" },
    ],
  },
  {
    id: "hugin_3000",
    label: "Kongsberg HUGIN 3000",
    specFile: "hugin_3000.yaml",
    toolsCompiled: 9,
    sensors: [
      { name: "SAS", detail: "Synthetic Aperture Sonar" },
      { name: "MBES", detail: "Multibeam echo sounder — bathymetry" },
      { name: "Optical", detail: "4K stereo camera" },
      { name: "ADCP", detail: "Acoustic Doppler Current Profiler" },
    ],
  },
];
