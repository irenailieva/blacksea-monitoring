import { useEffect, useRef, useState } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import { Crosshair, X } from 'lucide-react';

// Дефиниция на тип за Bounding Box (Ограничаваща кутия): масив от 4 числа [minLon, minLat, maxLon, maxLat]
export type BBox = [number, number, number, number];

// Свойства на компонента
interface AoiDrawToolProps {
    // Колбек функция, която се извиква при потвърждаване на нарисуваната зона (Area of Interest - AOI)
    onAoiConfirm: (bbox: BBox, aoi_name: string, display_name?: string) => void;
}

// Компонент за интерактивно чертане на зони на интерес (AOI) върху картата
export default function AoiDrawTool({ onAoiConfirm }: AoiDrawToolProps) {
    // Вземане на инстанцията на Leaflet картата
    const map = useMap();
    
    // Състояния (State)
    const [drawing, setDrawing] = useState(false); // Дали в момента потребителят чертае
    const [drawnRect, setDrawnRect] = useState<L.Rectangle | null>(null); // Запазен правоъгълник след чертане
    const [drawnBbox, setDrawnBbox] = useState<BBox | null>(null); // Координати на финалния правоъгълник
    const [displayName, setDisplayName] = useState(''); // Потребителско име на зоната
    
    // Референции (Refs) за съхранение на стойности между рендерите без предизвикване на пререндериране
    const startLatLng = useRef<L.LatLng | null>(null); // Начална точка при натискане на мишката
    const rectRef = useRef<L.Rectangle | null>(null); // Текущ правоъгълник, който се чертае

    // Почистване при демонтиране (unmount) на компонента
    useEffect(() => {
        return () => {
            rectRef.current?.remove();
        };
    }, []);

    // Функция за изчистване на нарисуваното от картата и възстановяване на началното състояние
    const clearRect = () => {
        rectRef.current?.remove();
        rectRef.current = null;
        drawnRect?.remove();
        setDrawnRect(null);
        setDrawnBbox(null);
        setDisplayName('');
    };

    // Стартиране на процеса по чертане
    const startDrawing = () => {
        clearRect(); // Изчистване на предишни рисунки
        setDrawing(true);
        // Смяна на курсора на мишката
        map.getContainer().style.cursor = 'crosshair';
        // Деактивиране на влаченето на картата, за да може мишката да чертае
        map.dragging.disable();

        // Обработка на събитието при натискане на бутона на мишката върху картата
        const onMouseDown = (e: L.LeafletMouseEvent) => {
            startLatLng.current = e.latlng; // Записване на началната точка

            // Създаване на начален правоъгълник (точка) със сини стилове
            const rect = L.rectangle([e.latlng, e.latlng], {
                color: '#3b82f6',
                weight: 2,
                dashArray: '6 4', // Прекъсната линия
                fillColor: '#3b82f6',
                fillOpacity: 0.15,
            }).addTo(map);
            rectRef.current = rect;

            // Обработка на движението на мишката (динамично преоразмеряване)
            const onMouseMove = (ev: L.LeafletMouseEvent) => {
                if (startLatLng.current) {
                    // Актуализиране на границите на правоъгълника въз основа на началната и текущата точка
                    rect.setBounds(L.latLngBounds(startLatLng.current, ev.latlng));
                }
            };

            // Обработка на пускането на бутона на мишката (край на чертането)
            const onMouseUp = (ev: L.LeafletMouseEvent) => {
                // Премахване на слушателите на събития
                map.off('mousemove', onMouseMove);
                map.off('mouseup', onMouseUp);
                map.off('mousedown', onMouseDown);
                // Възстановяване на нормалното състояние на картата
                map.getContainer().style.cursor = '';
                map.dragging.enable();
                setDrawing(false);

                if (!startLatLng.current) return;
                // Изчисляване на крайното Bounding Box (BBox)
                const bounds = L.latLngBounds(startLatLng.current, ev.latlng);
                const sw = bounds.getSouthWest(); // Югозападен ъгъл
                const ne = bounds.getNorthEast(); // Североизточен ъгъл
                const bbox: BBox = [
                    Math.min(sw.lng, ne.lng),
                    Math.min(sw.lat, ne.lat),
                    Math.max(sw.lng, ne.lng),
                    Math.max(sw.lat, ne.lat),
                ];
                setDrawnRect(rect);
                setDrawnBbox(bbox);
                startLatLng.current = null;
            };

            // Закачане на слушателите към картата
            map.on('mousemove', onMouseMove);
            map.on('mouseup', onMouseUp);
        };

        map.on('mousedown', onMouseDown);
    };

    // Функция за отказване от чертането
    const cancelDrawing = () => {
        setDrawing(false);
        map.getContainer().style.cursor = '';
        map.dragging.enable();
        clearRect();
        map.off('mousedown');
        map.off('mousemove');
        map.off('mouseup');
    };

    // Функция за потвърждаване на нарисуваната зона и изпращането ѝ към родителския компонент
    const confirmAoi = () => {
        if (!drawnBbox) return;
        // Автоматично генериране на уникално име въз основа на координатите
        const name = `AOI_${drawnBbox[0].toFixed(3)}_${drawnBbox[1].toFixed(3)}`;
        onAoiConfirm(drawnBbox, name, displayName || undefined);
        clearRect(); // Изчистване след успешно потвърждение
    };

    return (
        <>
            {/* Бутон за чертане, позициониран горе вляво на картата */}
            <div className="leaflet-top leaflet-left" style={{ marginTop: '10px', marginLeft: '10px', zIndex: 1000 }}>
                <div className="leaflet-control" style={{ pointerEvents: 'auto' }}>
                    {/* Ако не се чертае в момента и няма нарисувана кутия, показваме бутона 'Analyze Area' */}
                    {!drawing && !drawnBbox && (
                        <button
                            onClick={startDrawing}
                            title="Draw AOI and analyze"
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                                background: 'white',
                                border: '2px solid #3b82f6',
                                borderRadius: '6px',
                                padding: '6px 12px',
                                fontSize: '12px',
                                fontWeight: 600,
                                color: '#1d4ed8',
                                cursor: 'pointer',
                                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                                whiteSpace: 'nowrap',
                            }}
                        >
                            <Crosshair size={14} />
                            Анализирай Зона
                        </button>
                    )}

                    {/* Докато се чертае, показваме инструкция */}
                    {drawing && (
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            background: '#eff6ff',
                            border: '2px solid #3b82f6',
                            borderRadius: '6px',
                            padding: '6px 12px',
                            fontSize: '12px',
                            fontWeight: 600,
                            color: '#1d4ed8',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                        }}>
                            <Crosshair size={14} className="animate-pulse" />
                            Кликнете и плъзнете, за да очертаете зона
                            <button onClick={cancelDrawing} style={{ marginLeft: 4, cursor: 'pointer', background: 'none', border: 'none', color: '#6b7280' }}>
                                <X size={14} />
                            </button>
                        </div>
                    )}

                    {/* След като имаме нарисуван правоъгълник, показваме форма за потвърждение */}
                    {drawnBbox && !drawing && (
                        <div style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '8px',
                            background: 'white',
                            border: '2px solid #3b82f6',
                            borderRadius: '6px',
                            padding: '10px',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                            width: '260px',
                            pointerEvents: 'auto',
                        }}>
                            <div style={{ fontSize: '11px', fontWeight: 600, color: '#374151' }}>
                                Име на зоната (опционално):
                            </div>
                            <input
                                type="text"
                                value={displayName}
                                onChange={(e) => setDisplayName(e.target.value)}
                                placeholder="напр. Варненско езеро"
                                style={{
                                    width: '100%',
                                    padding: '4px 8px',
                                    fontSize: '12px',
                                    border: '1px solid #d1d5db',
                                    borderRadius: '4px',
                                    color: '#1f2937',
                                    outline: 'none',
                                }}
                            />
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px',
                                width: '100%',
                            }}>
                                <button
                                    onClick={confirmAoi}
                                    style={{
                                        flex: 1,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: '6px',
                                        background: '#1d4ed8',
                                        border: 'none',
                                        borderRadius: '6px',
                                        padding: '6px 10px',
                                        fontSize: '12px',
                                        fontWeight: 700,
                                        color: 'white',
                                        cursor: 'pointer',
                                    }}
                                >
                                    ✓ Анализирай
                                </button>
                                <button
                                    onClick={clearRect}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: '4px',
                                        background: 'white',
                                        border: '1px solid #d1d5db',
                                        borderRadius: '6px',
                                        padding: '6px 10px',
                                        fontSize: '12px',
                                        color: '#6b7280',
                                        cursor: 'pointer',
                                    }}
                                >
                                    Отказ
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}
