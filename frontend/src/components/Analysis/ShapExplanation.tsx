import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Cell } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

import { useEffect, useState } from 'react';
import api from '@/api/axios';
import { Loader2 } from 'lucide-react';

interface ShapData {
    feature: string;
    value: number;
}

interface ShapExplanationProps {
    regionId?: string;
}

export function ShapExplanation({ regionId }: ShapExplanationProps) {
    const [shapData, setShapData] = useState<ShapData[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!regionId) return;

        const fetchShap = async () => {
            setLoading(true);
            try {
                const response = await api.get<ShapData[]>('/analysis/shap-values', {
                    params: { region_id: regionId }
                });
                setShapData(response.data);
            } catch (error) {
                console.error('Failed to fetch SHAP values:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchShap();
    }, [regionId]);

    return (
        <Card className="col-span-1 lg:col-span-1">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle>Model Explainability (SHAP)</CardTitle>
                        <CardDescription>
                            Feature importance for current classification
                        </CardDescription>
                    </div>
                    {loading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
                </div>
            </CardHeader>
            <CardContent className="pb-4">
                <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={shapData} layout="vertical" margin={{ top: 0, right: 0, left: 40, bottom: 0 }}>
                            <XAxis type="number" hide />
                            <YAxis
                                dataKey="feature"
                                type="category"
                                width={80}
                                tick={{ fontSize: 11 }}
                                tickLine={false}
                                axisLine={false}
                            />
                            <Tooltip
                                cursor={{ fill: 'transparent' }}
                                contentStyle={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e5e7eb' }}
                            />
                            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                {shapData.map((entry, index) => (
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
