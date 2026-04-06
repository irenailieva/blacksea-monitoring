import { MapContainer, TileLayer, Polygon, Popup, LayersControl } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Region } from '../../api/types';
import L from 'leaflet';

// Fix for default marker icon in Leaflet + React
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

import ClassificationOverlay from './ClassificationOverlay';
import MapLegend from './MapLegend';

interface MapProps {
    regions: Region[];
    selectedSceneUrl?: string;
}

export default function AppMap({ regions, selectedSceneUrl }: MapProps) {
    // Center of Black Sea approx
    const center: [number, number] = [43.0, 27.9]; // Adjusted to Bulgarian coast

    return (
        <div className="h-full w-full rounded-lg overflow-hidden border">
            <MapContainer center={center} zoom={9} scrollWheelZoom={true} className="h-full w-full">
                <LayersControl position="topright">
                    <LayersControl.BaseLayer checked name="OpenStreetMap">
                        <TileLayer
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        />
                    </LayersControl.BaseLayer>
                    <LayersControl.BaseLayer name="Satellite (Esri)">
                        <TileLayer
                            attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                        />
                    </LayersControl.BaseLayer>
                    <LayersControl.BaseLayer name="Hydrography (Esri Ocean)">
                        <TileLayer
                            attribution='Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA, CHS, OSU, UNH, CSUMB, National Geographic, DeLorme, NAVTEQ, and Esri'
                            url="https://services.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}"
                        />
                    </LayersControl.BaseLayer>
                    <LayersControl.Overlay name="Sea Markers (OpenSeaMap)">
                        <TileLayer
                            url="https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png"
                            attribution='Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors'
                        />
                    </LayersControl.Overlay>
                </LayersControl>

                {selectedSceneUrl && (
                    <>
                        <ClassificationOverlay url={selectedSceneUrl} />
                        <MapLegend />
                    </>
                )}

                {regions.filter(r => r.geometry).map((region) => (
                    <Polygon
                        key={region.id}
                        pathOptions={{ color: 'blue', fillColor: 'blue', fillOpacity: 0.1 }}
                        positions={region.geometry!.coordinates[0].map(coord => [coord[1], coord[0]] as [number, number])} // GeoJSON is [lng, lat], Leaflet is [lat, lng]
                    >
                        <Popup>
                            <div className="p-1 min-w-[150px]">
                                <h3 className="font-bold text-sm border-b pb-1 mb-2">{region.name}</h3>
                                <div className="space-y-1.5">
                                    <div className="flex justify-between text-[10px] text-muted-foreground uppercase">
                                        <span>Type</span>
                                        <span className="font-mono">{region.type}</span>
                                    </div>
                                    <div className="flex justify-between text-[10px] text-muted-foreground uppercase">
                                        <span>Avg. Depth</span>
                                        <span className="font-mono">12.5m</span>
                                    </div>
                                    <div className="mt-2 pt-2 border-t flex flex-col gap-1.5">
                                        <div className="flex justify-between text-xs">
                                            <span className="text-muted-foreground">Vegetation:</span>
                                            <span className="font-medium text-green-600">1,240m²</span>
                                        </div>
                                        <div className="flex justify-between text-xs">
                                            <span className="text-muted-foreground">Confidence:</span>
                                            <span className="font-medium">92%</span>
                                        </div>
                                        <div className="flex justify-between text-xs">
                                            <span className="text-muted-foreground">Last Scanned:</span>
                                            <span className="font-medium">2023-12-15</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </Popup>
                    </Polygon>
                ))}
            </MapContainer>
        </div>
    );
}
