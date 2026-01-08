import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, Cell } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

const data = [
    {
        feature: "NDWI",
        value: 0.45,
    },
    {
        feature: "Blue Band",
        value: 0.32,
    },
    {
        feature: "Green Band",
        value: 0.15,
    },
    {
        feature: "Red Band",
        value: -0.10,
    },
    {
        feature: "NIR",
        value: -0.25,
    },
]

export function ShapExplanation() {
    return (
        <Card className="col-span-1 lg:col-span-1">
            <CardHeader>
                <CardTitle>Model Explainability (SHAP)</CardTitle>
                <CardDescription>
                    Feature importance for current classification
                </CardDescription>
            </CardHeader>
            <CardContent className="pb-4">
                <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 0, left: 40, bottom: 0 }}>
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
                                {data.map((entry, index) => (
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
