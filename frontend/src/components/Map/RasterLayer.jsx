import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import parseGeoraster from 'georaster';
import GeoRasterLayer from 'georaster-layer-for-leaflet';

export default function RasterLayer({ url, opacity = 1 }) {
    const map = useMap();
    const layerRef = useRef(null);

    useEffect(() => {
        if (!url) return;

        const loadLayer = async () => {
            try {
                const response = await fetch(url);
                const arrayBuffer = await response.arrayBuffer();
                const georaster = await parseGeoraster(arrayBuffer);

                if (layerRef.current) {
                    map.removeLayer(layerRef.current);
                }

                const layer = new GeoRasterLayer({
                    georaster,
                    opacity,
                    resolution: 256,
                    // Custom color function for classification map
                    pixelValuesToColorFn: (values) => {
                        const val = values[0];
                        if (val === 10) return '#f4a460'; // Sand
                        if (val === 20) return '#00ff00'; // Algae
                        if (val === 30) return '#0000ff'; // Water
                        return null; // Transparent
                    }
                });

                layer.addTo(map);
                layerRef.current = layer;

                // Fit bounds to the raster
                map.fitBounds(layer.getBounds());

            } catch (error) {
                console.error("Failed to load generic raster:", error);
            }
        };

        loadLayer();

        return () => {
            if (layerRef.current) {
                map.removeLayer(layerRef.current);
            }
        };
    }, [url, map, opacity]);

    useEffect(() => {
        if (layerRef.current) {
            layerRef.current.setOpacity(opacity);
        }
    }, [opacity]);

    return null;
}
