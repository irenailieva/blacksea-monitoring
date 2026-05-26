import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polygon, Popup, LayersControl, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Region } from '../../api/types';
import L from 'leaflet';
import { Eye, EyeOff } from 'lucide-react';

// Импортиране на базови иконки за маркерите на Leaflet, тъй като по подразбиране React понякога губи пътя до тях
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

// Конфигуриране на глобалната иконка на Leaflet за всички маркери
let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

import ClassificationOverlay from './ClassificationOverlay';
import MapLegend from './MapLegend';
import AoiDrawTool, { BBox } from './AoiDrawTool';

// Свойства, очаквани от компонента Map
interface MapProps {
    regions: Region[]; // Списък с дефинирани региони (АОИ - Зони на интерес)
    selectedSceneUrl?: string; // URL адрес към сателитната снимка/класификация
    onAoiSubmit?: (bbox: BBox, aoi_name: string, display_name?: string) => void; // Функция при създаване на нов регион
}

// Помощен компонент: Отговаря за автоматичното преоразмеряване на картата при промяна на размера на контейнера ѝ
function MapResizer() {
    const map = useMap();
    useEffect(() => {
        // Използване на ResizeObserver за следене на промените в размера на DOM елемента на картата
        const resizeObserver = new ResizeObserver(() => {
            map.invalidateSize(); // Казва на Leaflet да преизчисли размерите си
        });
        const container = map.getContainer();
        resizeObserver.observe(container);
        
        // Почистване при демонтиране
        return () => {
            resizeObserver.unobserve(container);
            resizeObserver.disconnect();
        };
    }, [map]);
    return null; // Този компонент не рендира нищо визуално
}

// Главен компонент за картата
export default function AppMap({ regions, selectedSceneUrl, onAoiSubmit }: MapProps) {
    // Център на картата по подразбиране: Черноморското крайбрежие около Варна
    const center: [number, number] = [43.0, 27.9];
    
    // Състояние за скриване/показване на класификационния слой (Overlay)
    const [showOverlay, setShowOverlay] = useState(true);

    return (
        // Основен контейнер на картата (трябва да има зададена височина)
        <div className="relative h-full w-full rounded-lg overflow-hidden border">
            {/* Ако има заредена сцена, показваме бутон за превключване на видимостта ѝ */}
            {selectedSceneUrl && (
                <div className="absolute top-[70px] right-2.5 z-[1000]">
                    <button
                        onClick={() => setShowOverlay(!showOverlay)}
                        className="bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 shadow-lg rounded flex items-center p-2 border border-slate-200 transition-colors"
                        title={showOverlay ? 'Hide Classification Overlay' : 'Show Classification Overlay'}
                    >
                        {showOverlay ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4 text-blue-600" />}
                    </button>
                </div>
            )}
            
            {/* Инстанциране на Leaflet картата */}
            <MapContainer center={center} zoom={9} scrollWheelZoom={true} className="h-full w-full">
                {/* Вмъкваме помощния компонент за преоразмеряване */}
                <MapResizer />
                
                {/* Контрол за управление на слоевете (Горе вдясно) */}
                <LayersControl position="topright">
                    {/* Базов слой: OpenStreetMap (По подразбиране) */}
                    <LayersControl.BaseLayer checked name="OpenStreetMap">
                        <TileLayer
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        />
                    </LayersControl.BaseLayer>
                    
                    {/* Базов слой: Сателитна снимка (Esri) */}
                    <LayersControl.BaseLayer name="Сателит (Esri)">
                        <TileLayer
                            attribution='Tiles &copy; Esri'
                            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                        />
                    </LayersControl.BaseLayer>
                    
                    {/* Базов слой: Хидрография (Дълбочини, релеф на дъното от Esri Ocean) */}
                    <LayersControl.BaseLayer name="Хидрография (Esri Ocean)">
                        <TileLayer
                            attribution='Tiles &copy; Esri'
                            url="https://services.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}"
                        />
                    </LayersControl.BaseLayer>
                    
                    {/* Допълнителен слой (Overlay) над базовия: Морски навигационни маркери */}
                    <LayersControl.Overlay name="Морски маркери (OpenSeaMap)">
                        <TileLayer
                            url="https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png"
                            attribution='Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors'
                        />
                    </LayersControl.Overlay>
                </LayersControl>

                {/* Инструмент за чертане на нов регион, ако е подадена onAoiSubmit функция */}
                {onAoiSubmit && <AoiDrawTool onAoiConfirm={onAoiSubmit} />}

                {/* Изобразяване на класификационния резултат от сателита (ако е избран) */}
                {selectedSceneUrl && (
                    <ClassificationOverlay url={selectedSceneUrl} opacity={showOverlay ? 0.8 : 0} />
                )}
                
                {/* Легенда за цветовете на класификацията */}
                {selectedSceneUrl && <MapLegend />}

                {/* Рендиране на полигоните на запазените региони */}
                {regions.filter(r => r.geometry).map((region) => (
                    <Polygon
                        key={region.id}
                        pathOptions={{ color: 'blue', fillColor: 'blue', fillOpacity: 0.1 }}
                        // Обръщане на координатите (GeoJSON използва [lng, lat], докато Leaflet иска [lat, lng])
                        positions={region.geometry!.coordinates[0].map(coord => [coord[1], coord[0]] as [number, number])}
                    >
                        {/* Изскачащ прозорец (Popup) при клик върху полигона */}
                        <Popup>
                            <div className="p-1 min-w-[150px]">
                                <h3 className="font-bold text-sm border-b pb-1 mb-2">{region.name}</h3>
                                <div className="space-y-1.5">
                                    <div className="flex justify-between text-[10px] text-muted-foreground uppercase">
                                        <span>Тип</span>
                                        <span className="font-mono">{region.type}</span>
                                    </div>
                                    <div className="mt-2 pt-2 border-t flex flex-col gap-1.5">
                                        <div className="flex justify-between text-xs">
                                            <span className="text-muted-foreground">Растителност:</span>
                                            {/* Хардкодирани данни за демонстрация (TODO: свързване с бекенда) */}
                                            <span className="font-medium text-green-600">1,240m²</span>
                                        </div>
                                        <div className="flex justify-between text-xs">
                                            <span className="text-muted-foreground">Увереност:</span>
                                            <span className="font-medium">92%</span>
                                        </div>
                                        <div className="flex justify-between text-xs">
                                            <span className="text-muted-foreground">Последно сканиран:</span>
                                            <span className="font-medium">2026-04-06</span>
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
