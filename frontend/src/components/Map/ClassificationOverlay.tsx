import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import proj4 from 'proj4';

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
    const layerRef = useRef<any>(null);

    useEffect(() => {
        if (!url) return;

        let activeLayer: any;
        let isActive = true; // Prevents React 18 strict mode from creating orphaned layers on unmount

        const cacheBusterUrl = `${url}?t=${new Date().getTime()}`;
        
        fetch(cacheBusterUrl)
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                return response.arrayBuffer();
            })
            .then(arrayBuffer => parseGeoraster(arrayBuffer))
            .then(georaster => {
                // If the component unmounted before the fetch finished, abort layering
                if (!isActive) return;

                // @ts-ignore
                activeLayer = new GeoRasterLayer({
                    georaster: georaster,
                    opacity: opacity, // Initial opacity
                    proj4: proj4,
                    zIndex: 1000,
                    pane: 'overlayPane',
                    pixelValuesToColorFn: (values: number[]) => {
                        const val = values[0];
                        
                        // 1. Strict discrete mapping 
                        if (val === 10 || val === 1) return '#facc15'; // Golden Yellow (Sand)
                        if (val === 20 || val === 2) return '#22c55e'; // Emerald Green (Algae)
                        if (val === 30 || val === 3) return '#0ea5e9'; // Hydro Blue (Water)
                        if (val === 255 || val === 0 || !val) return 'transparent';
                        
                        // 2. Categorical Quantizer (Catches floating point errors when over-zoomed)
                        const snappedVal = Math.round(val / 10) * 10;
                        if (snappedVal === 10) return '#facc15';
                        if (snappedVal === 20) return '#22c55e';
                        if (snappedVal === 30) return '#0ea5e9';

                        return 'transparent'; // Handles nodata correctly
                    },
                    resolution: 128, // Balances CPU rendering lag vs dropping thin features
                    maxNativeZoom: 14 // Sentinel-2 data is ~10m/px (approx zoom 14).
                });
                
                layerRef.current = activeLayer;
                activeLayer.addTo(map);
                
                const bounds = activeLayer.getBounds();
                if (bounds.isValid()) {
                    map.fitBounds(bounds, { animate: true, padding: [20, 20] });
                }
            })
            .catch(err => {
                if (isActive) {
                    console.error("💥 FAILED to load GeoTIFF classification:", url, err);
                }
            });

        return () => {
            isActive = false;
            layerRef.current = null;
            if (activeLayer && map) {
                map.removeLayer(activeLayer);
            }
        };
    }, [url, map]); // Removed `opacity` so that changing opacity doesn't re-mount and recenter the map!

    // Handle seamless opacity changes instantly without re-mounting or re-fetching
    useEffect(() => {
        if (layerRef.current) {
            layerRef.current.setOpacity(opacity);
        }
    }, [opacity]);

    return null;
}
