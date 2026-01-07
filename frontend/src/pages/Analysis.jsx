import { useState, useEffect } from 'react';
import TrendChart from '../components/Charts/TrendChart';
import api from '../lib/api';

export default function Analysis() {
    const [data, setData] = useState([]);
    const [indexTypes, setIndexTypes] = useState([]);
    const [selectedIndex, setSelectedIndex] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchIndexTypes();
    }, []);

    useEffect(() => {
        if (selectedIndex) {
            fetchData(selectedIndex);
        }
    }, [selectedIndex]);

    const fetchIndexTypes = async () => {
        try {
            const res = await api.get('/index-types/');
            setIndexTypes(res.data);
            if (res.data.length > 0) {
                setSelectedIndex(res.data[0].id);
            } else {
                setLoading(false);
            }
        } catch (error) {
            console.error("Failed to fetch index types:", error);
            setLoading(false);
        }
    };

    const fetchData = async (indexTypeId) => {
        setLoading(true);
        try {
            const res = await api.get('/index-values/', {
                params: { index_type_id: indexTypeId }
            });
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

    const selectedIndexName = indexTypes.find(t => t.id == selectedIndex)?.name || 'Index';

    return (
        <div className="p-8 h-full overflow-y-auto">
            <h1 className="text-3xl font-bold text-white mb-8">Water Quality Analysis</h1>

            <div className="mb-6">
                <label className="text-gray-400 mr-2">Select Index:</label>
                <select
                    className="bg-gray-800 text-white p-2 rounded border border-gray-700 focus:border-blue-500 outline-none"
                    value={selectedIndex}
                    onChange={(e) => setSelectedIndex(e.target.value)}
                    disabled={indexTypes.length === 0}
                >
                    {indexTypes.map(type => (
                        <option key={type.id} value={type.id}>{type.name}</option>
                    ))}
                    {indexTypes.length === 0 && <option>No indices found</option>}
                </select>
            </div>

            <div className="grid grid-cols-1 gap-8">
                {loading ? (
                    <p className="text-gray-400">Loading data...</p>
                ) : (
                    <TrendChart data={data} title={`${selectedIndexName} Trend`} />
                )}
            </div>

            <div className="mt-8 rounded-lg bg-blue-900/20 border border-blue-500/30 p-6">
                <h3 className="text-xl font-bold text-blue-400 mb-2">Analysis Summary</h3>
                <p className="text-gray-300">
                    {data.length > 0
                        ? `Trend analysis for ${selectedIndexName} showing ${data.length} data points.`
                        : "No data available for the selected index."}
                </p>
            </div>
        </div>
    );
}
