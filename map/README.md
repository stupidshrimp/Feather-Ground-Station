# Map assets

This directory holds third-party files required to display the map completely offline.
Copy the following files into this directory:

- `maplibre-gl.js` and `maplibre-gl.css` – MapLibre GL library
- `pmtiles.js` – Protomaps PMTiles reader
- `map1.pmtiles` – raster tiles bundle

The application uses the `map1.pmtiles` database exclusively and will not fetch tiles
from the internet. If this file is missing, the map area will show an error message.
