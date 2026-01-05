import { useState, useEffect } from 'react';
import TrendChart from '../components/Charts/TrendChart';
import api from '../lib/api';

export default function Analysis() {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Mock data for now, or fetch from backend
                // In reality, we'd fetch /index-values
                const mockData = [
                    { date: '2023-01-01', value: 0.2 },
                    { date: '2023-02-01', value: 0.3 },
                    { date: '2023-03-01', value: 0.25 },
                    { date: '2023-04-01', value: 0.4 },
                    { date: '2023-05-01', value: 0.35 },
                ];
                setData(mockData);
            } catch (error) {
                console.error("Failed to fetch analysis data:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    return (
        <div className="p-8 h-full overflow-y-auto">
            <h1 className="text-3xl font-bold text-white mb-8">Water Quality Analysis</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <TrendChart data={data} title="NDVI Trend (Mock Data)" />
                <TrendChart data={[]} title="Chlorophyll-a Trend (No Data)" />
            </div>

            <div className="mt-8 rounded-lg bg-blue-900/20 border border-blue-500/30 p-6">
                <h3 className="text-xl font-bold text-blue-400 mb-2">Analysis Summary</h3>
                <p className="text-gray-300">
                    Recent trends indicate stable water quality levels. NDVI values show seasonal fluctuations consistent with algae bloom patterns.
                    Further monitoring of Sector B is recommended.
                </p>
            </div>
        </div>
    );
}
