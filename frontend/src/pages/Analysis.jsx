import { useState, useEffect } from 'react';
import TrendChart from '../components/Charts/TrendChart';
import api from '../lib/api';

export default function Analysis() {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await api.get('/index-values/');
                const formattedData = res.data.map(item => ({
                    date: new Date(item.created_at).toLocaleDateString(),
                    value: item.mean_value
                }));
                // Sort by date usually good
                formattedData.sort((a, b) => new Date(a.date) - new Date(b.date));

                setData(formattedData);
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
                <TrendChart data={data} title="NDVI Trend" />
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
