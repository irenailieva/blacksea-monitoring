import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid, Legend } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

// Mock data
const data = [
    {
        date: "2024-01",
        vegetation: 2400,
        sand: 1398,
    },
    {
        date: "2024-02",
        vegetation: 2210,
        sand: 1500,
    },
    {
        date: "2024-03",
        vegetation: 2290,
        sand: 1450,
    },
    {
        date: "2024-04",
        vegetation: 2500,
        sand: 1300,
    },
    {
        date: "2024-05",
        vegetation: 2800,
        sand: 1100,
    },
    {
        date: "2024-06",
        vegetation: 3100,
        sand: 900,
    },
    {
        date: "2024-07",
        vegetation: 3400,
        sand: 850,
    },
]

interface VegetationChartProps {
    regionId?: string;
}

interface ShapExplanationProps {
    regionId?: string;
}

export function ShapExplanation({ regionId }: ShapExplanationProps) {
    // In a real app, use regionId to fetch SHAP values
    console.log('Fetching SHAP values for region:', regionId);
    return (
        <Card className="col-span-1 lg:col-span-2">
            <CardHeader>
                <CardTitle>SHAP Explanation</CardTitle>
                <CardDescription>
                    Feature importance for predictions
                </CardDescription>
            </CardHeader>
            <CardContent className="pb-4">
                <div className="h-[300px] flex items-center justify-center text-gray-500">
                    SHAP explanation chart will go here.
                </div>
            </CardContent>
        </Card>
    );
}

export function VegetationChart({ regionId }: VegetationChartProps) {
    // In a real app, use regionId to fetch specific data
    console.log('Fetching vegetation data for region:', regionId);
    return (
        <Card className="col-span-1 lg:col-span-2">
            <CardHeader>
                <CardTitle>Vegetation Trends</CardTitle>
                <CardDescription>
                    Area coverage (m²) over time
                </CardDescription>
            </CardHeader>
            <CardContent className="pb-4">
                <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
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
