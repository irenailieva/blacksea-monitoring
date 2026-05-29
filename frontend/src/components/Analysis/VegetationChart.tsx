import { useEffect, useState } from 'react';
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid, Legend } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2 } from 'lucide-react';
import api from '@/api/axios';

// Интерфейс, описващ данните за тенденциите (тренд) във времето
interface TrendData {
    date: string;
    vegetation: number;
    sand: number;
    water: number;
}


// Свойства: очакваме ID на регион, за който да покажем тенденциите
interface VegetationChartProps {
    regionId?: number | null;
}

// Компонент за визуализация на промяната в растителното покритие (времеви ред / Time Series)
export function VegetationChart({ regionId }: VegetationChartProps) {
    // Състояние за съхранение на данните за графиката
    const [trendData, setTrendData] = useState<TrendData[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Ако не е избран регион, не правим заявка към сървъра
        if (!regionId) return;

        const fetchTrends = async () => {
            setLoading(true);
            try {
                // Извличане на исторически данни (Time Series) от бекенда
                const response = await api.get<TrendData[]>('/analysis/vegetation-trend', {
                    params: { region_id: regionId }
                });
                setTrendData(response.data);
            } catch (error) {
                console.error('Неуспешно извличане на тенденциите за растителност:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchTrends();
    }, [regionId]); // Ефектът се задейства при промяна на избрания регион

    return (
        // Карточка, която заема две колони на големи екрани (по-широка от SHAP графиката)
        <Card className="col-span-1 lg:col-span-2">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle>Тенденции в растителността</CardTitle>
                        <CardDescription>
                            Площно покритие (km²) във времето
                        </CardDescription>
                    </div>
                    {/* Индикатор за зареждане */}
                    {loading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
                </div>
            </CardHeader>
            <CardContent className="pb-4">
                <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                        {/* 
                          Линейна графика. Преди визуализация данните (в кв.м.) 
                          се преобразуват в кв.км. за по-добра четимост.
                        */}
                        <LineChart 
                          data={trendData.length > 0 ? trendData.map(d => ({ 
                              ...d, 
                              vegetation: Number((d.vegetation / 1_000_000).toFixed(3)), 
                              sand: Number((d.sand / 1_000_000).toFixed(3)),
                              water: Number((d.water / 1_000_000).toFixed(3))
                          })) : []} 
                          margin={{ top: 5, right: 10, left: 10, bottom: 0 }}
                        >
                            {/* Фонова мрежа (само хоризонтални линии) */}
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                            {/* X-оста показва датите */}
                            <XAxis
                                dataKey="date"
                                stroke="#888888"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                            />
                            {/* Y-оста показва площта */}
                            <YAxis
                                stroke="#888888"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                                tickFormatter={(value) => `${value}km²`} // Добавяне на мерна единица
                            />
                            {/* Персонализирана подсказка (Tooltip) при посочване */}
                            <Tooltip
                                contentStyle={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                itemStyle={{ fontSize: '12px' }}
                                labelStyle={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}
                            />
                            <Legend wrapperStyle={{ paddingTop: '20px' }} />
                            {/* Линия за растителността */}
                            <Line
                                type="monotone"
                                dataKey="vegetation"
                                name="Растителност (km²)"
                                stroke="#16a34a"
                                strokeWidth={2}
                                dot={{ r: 3, fill: '#16a34a' }}
                                activeDot={{ r: 5 }}
                            />
                            {/* Линия за пясъка */}
                            <Line
                                type="monotone"
                                dataKey="sand"
                                name="Пясък/Абиотични (km²)"
                                stroke="#eab308"
                                strokeWidth={2}
                                dot={{ r: 3, fill: '#eab308' }}
                                activeDot={{ r: 5 }}
                            />
                            {/* Линия за вода */}
                            <Line
                                type="monotone"
                                dataKey="water"
                                name="Вода (km²)"
                                stroke="#0ea5e9"
                                strokeWidth={2}
                                dot={{ r: 3, fill: '#0ea5e9' }}
                                activeDot={{ r: 5 }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    )
}
