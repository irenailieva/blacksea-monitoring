import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import proj4 from 'proj4';
import L from 'leaflet';

// @ts-ignore
window.proj4 = proj4;

// @ts-ignore
import parseGeoraster from 'georaster';
import GeoRasterLayer from 'georaster-layer-for-leaflet';

interface ClassificationOverlayProps {
    url: string;
    opacity?: number;
}

export default function ClassificationOverlay({ url, opacity = 0.8 }: ClassificationOverlayProps) {
    const map = useMap();

    useEffect(() => {
        if (!url) return;

        let layer: any;

        fetch(url)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.arrayBuffer();
            })
            .then(arrayBuffer => parseGeoraster(arrayBuffer))
            .then(georaster => {
                // @ts-ignore
                layer = new GeoRasterLayer({
                    georaster: georaster,
                    opacity: opacity,
                    proj4: proj4,
                    zIndex: 1000,
                    pane: 'overlayPane',
                    pixelValuesToColorFn: (values: number[]) => {
                        const val = values[0];
                        // 255/0 are typical nodata
                        if (val === georaster.noDataValue || val === 255 || val === 0) return 'transparent';
                        
                        // Robust range-based mapping to handle different model versions (1,2,3 or 10,20,30)
                        if (val === 2 || (val >= 20 && val < 30)) return '#22c55e'; // Emerald Green (Algae)
                        if (val === 1 || (val >= 10 && val < 20)) return '#facc15'; // Golden Yellow (Sand)
                        if (val === 3 || (val >= 30 && val < 40)) return '#0ea5e9'; // Hydro Blue (Water)
                        
                        return 'transparent';
                    },
                    resolution: 256 // High resolution for scientific detail
                });
                
                layer.addTo(map);
                
                const bounds = layer.getBounds();
                if (bounds.isValid()) {
                    map.fitBounds(bounds, { animate: true, padding: [20, 20] });
                }
            })
            .catch(err => {
                console.error("💥 FAILED to load GeoTIFF classification:", url, err);
            });

        return () => {
            if (layer && map) map.removeLayer(layer);
        };
    }, [url, opacity, map]);

    return null;
}
