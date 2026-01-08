import { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import { GeoJSON } from 'react-leaflet';

export default function RegionsLayer({ regions, visible = true }) {
    const map = useMap();

    if (!regions || regions.length === 0 || !visible) {
        return null;
    }

    // Filter regions that have geometry
    const regionsWithGeometry = regions.filter(r => r.geometry);

    if (regionsWithGeometry.length === 0) {
        return null;
    }

    // Create GeoJSON features for each region
    const features = regionsWithGeometry.map(region => {
        // Ensure geometry is in correct format
        let geometry = region.geometry;
        if (geometry && geometry.coordinates && Array.isArray(geometry.coordinates[0])) {
            // If coordinates are already in correct format, use as is
            if (!Array.isArray(geometry.coordinates[0][0])) {
                // Wrap single ring in array for Polygon
                geometry = {
                    ...geometry,
                    coordinates: [geometry.coordinates]
                };
            }
        }
        
        return {
            type: 'Feature',
            properties: {
                id: region.id,
                name: region.name,
                type: region.type,
                description: region.description
            },
            geometry: geometry
        };
    });

    const geoJsonData = {
        type: 'FeatureCollection',
        features: features
    };

    // Style function based on region type
    const getStyle = (feature) => {
        const regionType = feature.properties.type;
        return {
            fillColor: regionType === 'aoi' ? '#3b82f6' : '#ef4444',
            fillOpacity: 0.2,
            color: regionType === 'aoi' ? '#3b82f6' : '#ef4444',
            weight: 2,
            opacity: 0.8
        };
    };

    // Event handlers
    const onEachFeature = (feature, layer) => {
        const { name, type, description } = feature.properties;
        const popupContent = `
            <div style="min-width: 200px;">
                <h3 style="margin: 0 0 8px 0; font-weight: bold; color: #1f2937;">${name}</h3>
                <p style="margin: 4px 0; color: #6b7280; font-size: 12px;">
                    <strong>Type:</strong> ${type}
                </p>
                ${description ? `<p style="margin: 4px 0; color: #6b7280; font-size: 12px;">${description}</p>` : ''}
            </div>
        `;
        layer.bindPopup(popupContent);
        
        // Highlight on hover
        layer.on({
            mouseover: (e) => {
                const layer = e.target;
                layer.setStyle({
                    weight: 3,
                    fillOpacity: 0.3
                });
            },
            mouseout: (e) => {
                const layer = e.target;
                layer.setStyle(getStyle(feature));
            }
        });
    };

    return (
        <GeoJSON
            data={geoJsonData}
            style={getStyle}
            onEachFeature={onEachFeature}
        />
    );
}
