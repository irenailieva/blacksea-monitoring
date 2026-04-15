import { useEffect, useState } from 'react';
import { ImageOverlay, useMap } from 'react-leaflet';
import proj4 from 'proj4';

// @ts-ignore
window.proj4 = proj4;

// @ts-ignore
import parseGeoraster from 'georaster';

interface ClassificationOverlayProps {
    url: string;
    opacity?: number;
}

export default function ClassificationOverlay({ url, opacity = 0.8 }: ClassificationOverlayProps) {
    const map = useMap();
    const [bounds, setBounds] = useState<[[number, number], [number, number]] | null>(null);
    const [pngUrl, setPngUrl] = useState<string | null>(null);

    useEffect(() => {
        if (!url) return;

        let isActive = true;
        const tifUrl = url.startsWith('http') ? url : `${import.meta.env.VITE_API_URL}${url.startsWith('/') ? '' : '/'}${url}`;
        const currentPngUrl = tifUrl.replace('.tif', '.png') + `?v=${Date.now()}`;

        // Fetch TIFF once to get spatial bounds for the ImageOverlay
        fetch(tifUrl)
            .then(res => res.arrayBuffer())
            .then(parseGeoraster)
            .then(georaster => {
                if (!isActive) return;
                
                const { xmin, ymin, xmax, ymax } = georaster;
                // Convert to Leaflet bounds [ [ymin, xmin], [ymax, xmax] ]
                const leafBounds: [[number, number], [number, number]] = [
                    [ymin, xmin],
                    [ymax, xmax]
                ];
                
                setBounds(leafBounds);
                setPngUrl(currentPngUrl);
                
                // One-time fit bounds on load
                map.fitBounds(leafBounds, { padding: [50, 50], animate: true });
            })
            .catch(err => console.error("💥 Failed to get bounds for overlay:", err));

        return () => {
            isActive = false;
        };
    }, [url, map]);

    if (!bounds || !pngUrl) return null;

    return (
        <ImageOverlay
            url={pngUrl}
            bounds={bounds}
            opacity={opacity}
            zIndex={1000}
        />
    );
}

