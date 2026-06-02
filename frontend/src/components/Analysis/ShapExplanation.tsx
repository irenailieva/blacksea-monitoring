import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Cell } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

import { useEffect, useState } from 'react';
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
                        <BarChart data={shapData} layout="vertical" margin={{ top: 0, right: 0, left: 40, bottom: 0 }}>
                            {/* Скрита X-ос (тъй като е хоризонтална графика) */}
                            <XAxis type="number" hide />
                            {/* Y-оста показва имената на характеристиките */}
                            <YAxis
                                dataKey="feature"
                                type="category"
                                width={80}
                                tick={{ fontSize: 11 }}
                                tickLine={false}
                                axisLine={false}
                            />
                            {/* Tooltip (подсказка) при посочване с мишката */}
                            <Tooltip
                                cursor={{ fill: 'transparent' }}
                                contentStyle={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb' }}
                            />
                            {/* Дефиниране на самите ленти (Bars) */}
                            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                {shapData.map((entry, index) => (
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
