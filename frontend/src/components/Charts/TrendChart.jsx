import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function TrendChart({ data, title }) {
    if (!data || data.length === 0) {
        return (
            <div className="flex h-64 items-center justify-center rounded-lg bg-gray-800 border border-gray-700">
                <p className="text-gray-400">No data available for {title}</p>
            </div>
        );
    }

    return (
        <div className="rounded-lg bg-gray-800 p-4 border border-gray-700 shadow-md">
            <h3 className="mb-4 text-lg font-bold text-white">{title}</h3>
            <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis
                            dataKey="date"
                            stroke="#9ca3af"
                            tick={{ fill: '#9ca3af' }}
                        />
                        <YAxis
                            stroke="#9ca3af"
                            tick={{ fill: '#9ca3af' }}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }}
                            itemStyle={{ color: '#fff' }}
                        />
                        <Legend wrapperStyle={{ color: '#fff' }} />
                        <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#3b82f6"
                            strokeWidth={2}
                            activeDot={{ r: 8 }}
                            name="Index Value"
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
