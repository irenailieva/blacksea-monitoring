const legendItems = [
    { label: 'Algae / Vegetation', color: '#22c55e', description: 'Undersea organic matter' },
    { label: 'Sand / Shallow', color: '#facc15', description: 'Sediments and shallow areas' },
    { label: 'Clear Water', color: '#0ea5e9', description: 'Deep or filtered water' },
];

export default function MapLegend() {
    return (
        <div className="absolute bottom-6 right-6 z-[1000] bg-background/90 backdrop-blur-md p-4 rounded-xl border shadow-2xl min-w-[200px] pointer-events-auto">
            <h4 className="text-sm font-bold mb-3 flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                Scientific Legend
            </h4>
            <div className="space-y-3">
                {legendItems.map((item) => (
                    <div key={item.label} className="flex items-center gap-3 group">
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
            <div className="mt-4 pt-4 border-t text-[9px] text-muted-foreground uppercase tracking-widest text-center font-bold">
                Classification Engine v1.0
            </div>
        </div>
    );
}
