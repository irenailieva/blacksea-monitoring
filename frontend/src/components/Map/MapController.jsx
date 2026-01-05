import { useEffect } from 'react';
import { useMap } from 'react-leaflet';

export default function MapController({ center, zoom }) {
    const map = useMap();

    useEffect(() => {
        if (center) {
            map.flyTo(center, zoom);
        }
    }, [center, zoom, map]);

    return null;
}
