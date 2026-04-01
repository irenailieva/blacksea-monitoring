import { useEffect } from 'react';
import { useMap } from 'react-leaflet';

import 'georaster-layer-for-leaflet';
// @ts-ignore
import parseGeoraster from 'georaster';

interface ClassificationOverlayProps {
    url: string;
    opacity?: number;
}

export default function ClassificationOverlay({ url, opacity = 0.7 }: ClassificationOverlayProps) {
    const map = useMap();

    useEffect(() => {
        if (!url) return;

        let layer: any;

        fetch(url)
            .then(response => response.arrayBuffer())
            .then(arrayBuffer => parseGeoraster(arrayBuffer))
            .then(georaster => {
                // @ts-ignore
                layer = new GeoRasterLayer({
                    georaster: georaster,
                    opacity: opacity,
                    pixelValuesToColorFn: (values: number[]) => {
                        const val = values[0];
                        // 1: Vegetation (Green), 2: Sand (Yellow), 3: Water (Blue/Transparent)
                        if (val === 1) return '#22c55e'; // Green
                        if (val === 2) return '#eab308'; // Yellow
                        if (val === 3) return 'transparent'; // Water
                        return 'transparent';
                    },
                    resolution: 64 // Adjust for performance
                });
                layer.addTo(map);

                // Fit bounds if it's the first layer or explicitly requested
                // map.fitBounds(layer.getBounds());
            })
            .catch(err => console.error("Error loading georaster:", err));

        return () => {
            if (layer) {
                map.removeLayer(layer);
            }
        };
    }, [url, opacity, map]);

    return null;
}
