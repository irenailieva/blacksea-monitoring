import { useState, useEffect } from 'react';
import api from '../lib/api';
import { Plus, Trash2, MapPin } from 'lucide-react';

export default function Regions() {
    const [regions, setRegions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [newRegion, setNewRegion] = useState({ name: '', type: 'aoi', coordinates: '' });
    const [error, setError] = useState('');

    useEffect(() => {
        fetchRegions();
    }, []);

    const fetchRegions = async () => {
        try {
            const res = await api.get('/regions/');
            setRegions(res.data);
        } catch (err) {
            console.error("Failed to fetch regions", err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        setError('');
        try {
            await api.post('/regions/', {
                ...newRegion,
                coordinates: JSON.parse(newRegion.coordinates || '[]') // Expecting JSON array for now
            });
            setNewRegion({ name: '', type: 'aoi', coordinates: '' });
            fetchRegions();
        } catch (err) {
            console.error(err);
            setError('Failed to create region. Ensure coordinates are valid JSON geometry/array.');
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('Are you sure?')) return;
        try {
            await api.delete(`/regions/${id}`);
            setRegions(regions.filter(r => r.id !== id));
        } catch (err) {
            console.error(err);
            alert('Failed to delete region');
        }
    };

    return (
        <div className="p-8 h-full overflow-y-auto">
            <h1 className="text-3xl font-bold text-white mb-8">Regions Management</h1>

            {/* Create Region Form */}
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 mb-8">
                <h2 className="text-xl font-semibold text-blue-400 mb-4 flex items-center gap-2">
                    <Plus className="w-5 h-5" /> Add New Region
                </h2>
                {error && <p className="text-red-400 mb-4">{error}</p>}
                <form onSubmit={handleCreate} className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <input
                        type="text"
                        placeholder="Region Name"
                        className="bg-gray-700 text-white rounded p-2 border border-gray-600 focus:border-blue-500 outline-none"
                        value={newRegion.name}
                        onChange={e => setNewRegion({ ...newRegion, name: e.target.value })}
                        required
                    />
                    <select
                        className="bg-gray-700 text-white rounded p-2 border border-gray-600 focus:border-blue-500 outline-none"
                        value={newRegion.type}
                        onChange={e => setNewRegion({ ...newRegion, type: e.target.value })}
                    >
                        <option value="aoi">AOI</option>
                        <option value="exclusion">Exclusion Zone</option>
                    </select>
                    <input
                        type="text"
                        placeholder='Coordinates (e.g. [[28,42],[29,42],...])'
                        className="bg-gray-700 text-white rounded p-2 border border-gray-600 focus:border-blue-500 outline-none md:col-span-1 lg:col-span-1"
                        value={newRegion.coordinates}
                        onChange={e => setNewRegion({ ...newRegion, coordinates: e.target.value })}
                    />
                    <button type="submit" className="bg-blue-600 text-white rounded p-2 font-semibold hover:bg-blue-700 transition">
                        Create Region
                    </button>
                </form>
            </div>

            {/* Regions List */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {loading ? (
                    <p className="text-gray-400">Loading regions...</p>
                ) : regions.length === 0 ? (
                    <p className="text-gray-500 italic">No regions found.</p>
                ) : (
                    regions.map(region => (
                        <div key={region.id} className="bg-gray-800 rounded-lg border border-gray-700 p-5 hover:border-blue-500/50 transition relative group">
                            <div className="flex justify-between items-start mb-2">
                                <h3 className="text-xl font-bold text-white max-w-[80%] truncate">{region.name}</h3>
                                <span className={`px-2 py-0.5 rounded text-xs uppercase font-bold ${region.type === 'aoi' ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'
                                    }`}>
                                    {region.type}
                                </span>
                            </div>

                            <div className="flex items-center text-gray-400 text-sm mb-4">
                                <MapPin className="w-4 h-4 mr-1" />
                                <span>ID: {region.id}</span>
                            </div>

                            <button
                                onClick={() => handleDelete(region.id)}
                                className="absolute top-4 right-4 text-gray-500 hover:text-red-500 opacity-0 group-hover:opacity-100 transition"
                            >
                                <Trash2 className="w-5 h-5" />
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
