import { useState, useEffect } from 'react';
import TrendChart from '../components/Charts/TrendChart';
import api from '../lib/api';
import { BarChart2, Filter, TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react';

export default function Analysis() {
    const [data, setData] = useState([]);
    const [indexTypes, setIndexTypes] = useState([]);
    const [regions, setRegions] = useState([]);
    const [selectedIndex, setSelectedIndex] = useState('');
    const [selectedRegion, setSelectedRegion] = useState(null);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState(null);

    useEffect(() => {
        fetchIndexTypes();
        fetchRegions();
    }, []);

    useEffect(() => {
        if (selectedIndex) {
            fetchData(selectedIndex);
        }
    }, [selectedIndex, selectedRegion]);

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

    const fetchRegions = async () => {
        try {
            const res = await api.get('/regions/');
            setRegions(res.data);
        } catch (error) {
            console.error("Failed to fetch regions:", error);
        }
    };

    const fetchData = async (indexTypeId) => {
        setLoading(true);
        try {
            const params = { index_type_id: indexTypeId };
            if (selectedRegion) {
                params.region_id = selectedRegion.id;
            }
            
            const res = await api.get('/index-values/', { params });
            const formattedData = res.data.map(item => ({
                date: new Date(item.created_at).toLocaleDateString(),
                value: item.mean_value,
                min: item.min_value,
                max: item.max_value
            }));
            
            // Sort by date
            formattedData.sort((a, b) => new Date(a.date) - new Date(b.date));

            setData(formattedData);
            calculateStats(formattedData);
        } catch (error) {
            console.error("Failed to fetch analysis data:", error);
        } finally {
            setLoading(false);
        }
    };

    const calculateStats = (dataPoints) => {
        if (dataPoints.length === 0) {
            setStats(null);
            return;
        }

        const values = dataPoints.map(d => d.value).filter(v => v !== null && v !== undefined);
        if (values.length === 0) {
            setStats(null);
            return;
        }

        const mean = values.reduce((a, b) => a + b, 0) / values.length;
        const min = Math.min(...values);
        const max = Math.max(...values);
        const sorted = [...values].sort((a, b) => a - b);
        const median = sorted.length % 2 === 0
            ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
            : sorted[Math.floor(sorted.length / 2)];

        // Calculate trend (comparing first half to second half)
        let trend = 'stable';
        if (values.length >= 4) {
            const firstHalf = values.slice(0, Math.floor(values.length / 2));
            const secondHalf = values.slice(Math.floor(values.length / 2));
            const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
            const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
            const change = ((secondAvg - firstAvg) / firstAvg) * 100;
            
            if (change > 5) trend = 'increasing';
            else if (change < -5) trend = 'decreasing';
        }

        setStats({ mean, min, max, median, trend, count: values.length });
    };

    const selectedIndexName = indexTypes.find(t => t.id == selectedIndex)?.name || 'Index';

    return (
        <div className="p-8 h-full overflow-y-auto">
            <div className="flex items-center gap-3 mb-8">
                <BarChart2 className="w-8 h-8 text-blue-400" />
                <h1 className="text-3xl font-bold text-white">Water Quality Analysis</h1>
            </div>

            {/* Filters */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
                        <Activity className="w-4 h-4" />
                        Select Index
                    </label>
                    <select
                        className="w-full bg-gray-800 text-white p-2 rounded border border-gray-700 focus:border-blue-500 outline-none"
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

                <div>
                    <label className="block text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
                        <Filter className="w-4 h-4" />
                        Filter by Region
                    </label>
                    <select
                        className="w-full bg-gray-800 text-white p-2 rounded border border-gray-700 focus:border-blue-500 outline-none"
                        value={selectedRegion?.id || ''}
                        onChange={(e) => {
                            const regionId = parseInt(e.target.value);
                            setSelectedRegion(regions.find(r => r.id === regionId) || null);
                        }}
                    >
                        <option value="">All Regions</option>
                        {regions.map(region => (
                            <option key={region.id} value={region.id}>{region.name}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Statistics Cards */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
                    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                        <div className="text-xs text-gray-400 mb-1">Mean Value</div>
                        <div className="text-2xl font-bold text-white">{stats.mean.toFixed(3)}</div>
                    </div>
                    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                        <div className="text-xs text-gray-400 mb-1">Median</div>
                        <div className="text-2xl font-bold text-white">{stats.median.toFixed(3)}</div>
                    </div>
                    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                        <div className="text-xs text-gray-400 mb-1">Min / Max</div>
                        <div className="text-lg font-semibold text-white">
                            {stats.min.toFixed(3)} / {stats.max.toFixed(3)}
                        </div>
                    </div>
                    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                        <div className="text-xs text-gray-400 mb-1">Data Points</div>
                        <div className="text-2xl font-bold text-white">{stats.count}</div>
                    </div>
                    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                        <div className="text-xs text-gray-400 mb-1">Trend</div>
                        <div className="flex items-center gap-2">
                            {stats.trend === 'increasing' && <TrendingUp className="w-5 h-5 text-green-400" />}
                            {stats.trend === 'decreasing' && <TrendingDown className="w-5 h-5 text-red-400" />}
                            {stats.trend === 'stable' && <Minus className="w-5 h-5 text-gray-400" />}
                            <span className="text-lg font-semibold text-white capitalize">{stats.trend}</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Chart */}
            <div className="mb-8">
                {loading ? (
                    <div className="flex h-64 items-center justify-center rounded-lg bg-gray-800 border border-gray-700">
                        <p className="text-gray-400">Loading data...</p>
                    </div>
                ) : (
                    <TrendChart data={data} title={`${selectedIndexName} Trend${selectedRegion ? ` - ${selectedRegion.name}` : ''}`} />
                )}
            </div>

            {/* Summary */}
            <div className="rounded-lg bg-blue-900/20 border border-blue-500/30 p-6">
                <h3 className="text-xl font-bold text-blue-400 mb-2">Analysis Summary</h3>
                <p className="text-gray-300">
                    {data.length > 0
                        ? `Trend analysis for ${selectedIndexName}${selectedRegion ? ` in ${selectedRegion.name}` : ''} showing ${data.length} data points.`
                        : "No data available for the selected index and region combination."}
                </p>
                {stats && (
                    <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                            <span className="text-gray-400">Mean:</span>
                            <span className="text-white ml-2 font-semibold">{stats.mean.toFixed(3)}</span>
                        </div>
                        <div>
                            <span className="text-gray-400">Range:</span>
                            <span className="text-white ml-2 font-semibold">{stats.min.toFixed(3)} - {stats.max.toFixed(3)}</span>
                        </div>
                        <div>
                            <span className="text-gray-400">Median:</span>
                            <span className="text-white ml-2 font-semibold">{stats.median.toFixed(3)}</span>
                        </div>
                        <div>
                            <span className="text-gray-400">Trend:</span>
                            <span className="text-white ml-2 font-semibold capitalize">{stats.trend}</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
