const legendItems = [
    { label: 'Algae / Vegetation', color: '#22c55e', description: 'Submerged organic matter' },
    { label: 'Sand / Shallows', color: '#facc15', description: 'Sediments and shallow zones' },
    { label: 'Open Water', color: '#0ea5e9', description: 'Deep or clear water' },
    { label: 'Marine Phytoplankton', color: '#06b6d4', description: 'Natural sea blooms (e.g., E. huxleyi)' },
];

// Компонент, визуализиращ легенда върху картата
export default function MapLegend() {
    return (
        // Позициониране долу вдясно (absolute), висок z-index и стъклен ефект (backdrop-blur)
        <div className="absolute bottom-6 right-6 z-[1000] bg-background/90 backdrop-blur-md p-4 rounded-xl border shadow-2xl min-w-[200px] pointer-events-auto">
            {/* Заглавие на легендата с пулсиращ индикатор */}
            <h4 className="text-sm font-bold mb-3 flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                Scientific Legend
            </h4>
            
            {/* Списък с елементите на легендата */}
            <div className="space-y-3">
                {legendItems.map((item) => (
                    // Всеки елемент от легендата: квадратно поле с цвят и текстов етикет
                    <div key={item.label} className="flex items-center gap-3 group">
                        {/* Цветен индикатор с ефект на мащабиране при посочване (hover) */}
                        <div 
                            className="h-4 w-4 rounded-sm border shadow-sm transition-transform group-hover:scale-110" 
                            style={{ backgroundColor: item.color }} 
                        />
                        <div className="flex flex-col">
                            <span className="text-xs font-semibold">{item.label}</span>
                            <span className="text-[10px] text-muted-foreground leading-tight italic">
                                {item.description}
                            </span>
                        </div>
                    </div>
                ))}
            </div>
            
            {/* Версия на класификатора (долен колонтип) */}
            <div className="mt-4 pt-4 border-t text-[9px] text-muted-foreground uppercase tracking-widest text-center font-bold">
                Classification Engine v1.0
            </div>
        </div>
    );
}
