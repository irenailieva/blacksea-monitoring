import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Cell, LabelList } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

import { useEffect, useState, useMemo } from 'react';
import api from '@/api/axios';
import { Loader2 } from 'lucide-react';

// Интерфейс, описващ структурата на една SHAP стойност
interface ShapData {
    feature: string; // Име на характеристиката (напр. NDWI, спектрална лента)
    value: number; // Влияние (тежест) върху предвиждането на модела
}

// Свойства на компонента: може да работи с ID на регион или ID на конкретна сцена
interface ShapExplanationProps {
    regionId?: string;
    sceneId?: number;
}

// Компонент за визуализация на SHAP (SHapley Additive exPlanations) стойности
// SHAP се използва за обяснимост на ML моделите (Model Explainability)
export function ShapExplanation({ regionId, sceneId }: ShapExplanationProps) {
    // Състояние за съхранение на данните за графиката
    const [shapData, setShapData] = useState<ShapData[]>([]);
    // Състояние за индикатор за зареждане
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Ако няма подаден регион или сцена, не изпълняваме заявка
        if (!regionId && !sceneId) return;

        // Асинхронна функция за извличане на SHAP стойностите от API-то
        const fetchShap = async () => {
            setLoading(true);
            try {
                const response = await api.get<ShapData[]>('/analysis/shap-values', {
                    // Ако е подадена сцена, използваме нея, иначе използваме региона
                    params: sceneId ? { scene_id: sceneId } : { region_id: regionId }
                });
                setShapData(response.data);
            } catch (error) {
                console.error('Failed to fetch SHAP values:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchShap();
    }, [regionId, sceneId]); // Ефектът се задейства при промяна на ID-то

    // Нормализиране на SHAP стойностите до процентни стойности (сума от абсолютните = 100%)
    // и закръгляне до цели числа за по-чист визуален изглед
    const chartData = useMemo(() => {
        if (shapData.length === 0) return [];
        const totalAbsolute = shapData.reduce((sum, d) => sum + Math.abs(d.value), 0);
        if (totalAbsolute === 0) return shapData.map(d => ({ ...d, value: 0 }));
        return shapData.map(d => ({
            ...d,
            value: Math.round((d.value / totalAbsolute) * 100),
        }));
    }, [shapData]);

    return (
        <Card className="col-span-1 lg:col-span-1">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle>Model Explainability (SHAP)</CardTitle>
                        <CardDescription>
                            Feature importance for the current classification
                        </CardDescription>
                    </div>
                    {/* Визуализация на спинър, докато се зареждат данните */}
                    {loading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
                </div>
            </CardHeader>
            <CardContent className="pb-4">
                <div className="h-[300px]">
                    {/* Контейнер, който автоматично оразмерява графиката */}
                    <ResponsiveContainer width="100%" height="100%">
                        {/* Хоризонтална лентова графика (BarChart) */}
                        <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 40, left: 40, bottom: 0 }}>
                            {/* X-оста показва процентните стойности като цели числа */}
                            <XAxis
                                type="number"
                                tickFormatter={(v: number) => `${Math.round(v)}%`}
                                tick={{ fontSize: 11 }}
                                axisLine={false}
                                tickLine={false}
                            />
                            {/* Y-оста показва имената на характеристиките */}
                            <YAxis
                                dataKey="feature"
                                type="category"
                                width={80}
                                tick={{ fontSize: 11 }}
                                tickLine={false}
                                axisLine={false}
                            />
                            {/* Tooltip (подсказка) при посочване с мишката — стойности като цели проценти */}
                            <Tooltip
                                cursor={{ fill: 'transparent' }}
                                contentStyle={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb' }}
                                formatter={(value: number) => [`${Math.round(value)}%`, 'Contribution']}
                            />
                            {/* Дефиниране на самите ленти (Bars) */}
                            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                {/* Етикети върху всяка лента с процентната стойност */}
                                <LabelList
                                    dataKey="value"
                                    position="right"
                                    formatter={(v: number) => `${Math.round(v)}%`}
                                    style={{ fontSize: 11, fill: '#6b7280' }}
                                />
                                {chartData.map((entry, index) => (
                                    // Оцветяване според стойността: зелено за положително влияние, червено за отрицателно
                                    <Cell key={`cell-${index}`} fill={entry.value > 0 ? "#16a34a" : "#ef4444"} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    )
}
