import { useEffect, useRef, useState } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import { Crosshair, X } from 'lucide-react';

export type BBox = [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]

interface AoiDrawToolProps {
    onAoiConfirm: (bbox: BBox, aoi_name: string, display_name?: string) => void;
}

export default function AoiDrawTool({ onAoiConfirm }: AoiDrawToolProps) {
    const map = useMap();
    const [drawing, setDrawing] = useState(false);
    const [drawnRect, setDrawnRect] = useState<L.Rectangle | null>(null);
    const [drawnBbox, setDrawnBbox] = useState<BBox | null>(null);
    const [displayName, setDisplayName] = useState('');
    const startLatLng = useRef<L.LatLng | null>(null);
    const rectRef = useRef<L.Rectangle | null>(null);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            rectRef.current?.remove();
        };
    }, []);

    const clearRect = () => {
        rectRef.current?.remove();
        rectRef.current = null;
        drawnRect?.remove();
        setDrawnRect(null);
        setDrawnBbox(null);
        setDisplayName('');
    };

    const startDrawing = () => {
        clearRect();
        setDrawing(true);
        map.getContainer().style.cursor = 'crosshair';
        map.dragging.disable();

        const onMouseDown = (e: L.LeafletMouseEvent) => {
            startLatLng.current = e.latlng;

            const rect = L.rectangle([e.latlng, e.latlng], {
                color: '#3b82f6',
                weight: 2,
                dashArray: '6 4',
                fillColor: '#3b82f6',
                fillOpacity: 0.15,
            }).addTo(map);
            rectRef.current = rect;

            const onMouseMove = (ev: L.LeafletMouseEvent) => {
                if (startLatLng.current) {
                    rect.setBounds(L.latLngBounds(startLatLng.current, ev.latlng));
                }
            };

            const onMouseUp = (ev: L.LeafletMouseEvent) => {
                map.off('mousemove', onMouseMove);
                map.off('mouseup', onMouseUp);
                map.off('mousedown', onMouseDown);
                map.getContainer().style.cursor = '';
                map.dragging.enable();
                setDrawing(false);

                if (!startLatLng.current) return;
                const bounds = L.latLngBounds(startLatLng.current, ev.latlng);
                const sw = bounds.getSouthWest();
                const ne = bounds.getNorthEast();
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

            map.on('mousemove', onMouseMove);
            map.on('mouseup', onMouseUp);
        };

        map.on('mousedown', onMouseDown);
    };

    const cancelDrawing = () => {
        setDrawing(false);
        map.getContainer().style.cursor = '';
        map.dragging.enable();
        clearRect();
        map.off('mousedown');
        map.off('mousemove');
        map.off('mouseup');
    };

    const confirmAoi = () => {
        if (!drawnBbox) return;
        const name = `AOI_${drawnBbox[0].toFixed(3)}_${drawnBbox[1].toFixed(3)}`;
        onAoiConfirm(drawnBbox, name, displayName || undefined);
        clearRect();
    };

    return (
        <>
            {/* Draw button — top-left of map */}
            <div className="leaflet-top leaflet-left" style={{ marginTop: '10px', marginLeft: '10px', zIndex: 1000 }}>
                <div className="leaflet-control" style={{ pointerEvents: 'auto' }}>
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
                            Analyze Area
                        </button>
                    )}

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
                            Click and drag to draw AOI
                            <button onClick={cancelDrawing} style={{ marginLeft: 4, cursor: 'pointer', background: 'none', border: 'none', color: '#6b7280' }}>
                                <X size={14} />
                            </button>
                        </div>
                    )}

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
                                Scene Display Name (optional):
                            </div>
                            <input
                                type="text"
                                value={displayName}
                                onChange={(e) => setDisplayName(e.target.value)}
                                placeholder="e.g. Lake Vaya"
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
                                    ✓ Analyze
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
                                    Cancel
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}
