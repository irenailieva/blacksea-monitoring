import { useEffect, useState } from 'react';
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid, Legend } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2 } from 'lucide-react';
import api from '@/api/axios';

// Mock data

interface TrendData {
    date: string;
    vegetation: number;
    sand: number;
}

interface VegetationChartProps {
    regionId?: number | null;
}

export function VegetationChart({ regionId }: VegetationChartProps) {
    const [trendData, setTrendData] = useState<TrendData[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!regionId) return;

        const fetchTrends = async () => {
            setLoading(true);
            try {
                const response = await api.get<TrendData[]>('/analysis/vegetation-trend', {
                    params: { region_id: regionId }
                });
                setTrendData(response.data);
            } catch (error) {
                console.error('Failed to fetch vegetation trends:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchTrends();
    }, [regionId]);

    return (
        <Card className="col-span-1 lg:col-span-2">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle>Vegetation Trends</CardTitle>
                        <CardDescription>
                            Area coverage (m²) over time
                        </CardDescription>
                    </div>
                    {loading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
                </div>
            </CardHeader>
            <CardContent className="pb-4">
                <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={trendData.length > 0 ? trendData : []} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                            <XAxis
                                dataKey="date"
                                stroke="#888888"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                            />
                            <YAxis
                                stroke="#888888"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                                tickFormatter={(value) => `${value}m²`}
                            />
                            <Tooltip
                                contentStyle={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                itemStyle={{ fontSize: '12px' }}
                                labelStyle={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}
                            />
                            <Legend wrapperStyle={{ paddingTop: '20px' }} />
                            <Line
                                type="monotone"
                                dataKey="vegetation"
                                stroke="#16a34a" // Green
                                strokeWidth={2}
                                dot={false}
                                activeDot={{ r: 4, fill: "#16a34a" }}
                            />
                            <Line
                                type="monotone"
                                dataKey="sand"
                                stroke="#eab308" // Yellow/Sand
                                strokeWidth={2}
                                dot={false}
                                activeDot={{ r: 4, fill: "#eab308" }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    )
}
