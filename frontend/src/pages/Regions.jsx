import { useState, useEffect } from 'react';
import api from '../lib/api';
import { Plus, Trash2, MapPin, Edit2, X, Save } from 'lucide-react';
import { useToast } from '../context/ToastContext';

export default function Regions() {
    const { success, error: showError } = useToast();
    const [regions, setRegions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [newRegion, setNewRegion] = useState({ name: '', type: 'aoi', coordinates: '' });
    const [editingRegion, setEditingRegion] = useState(null);
    const [editForm, setEditForm] = useState({ name: '', type: 'aoi', coordinates: '' });
    const [error, setError] = useState('');
    const [showCreateForm, setShowCreateForm] = useState(false);

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
            // Parse coordinates from string input "[[x,y],[x,y]]"
            const coords = JSON.parse(newRegion.coordinates || '[]');
            
            // Construct GeoJSON Polygon
            const geometry = {
                type: "Polygon",
                coordinates: [coords] // Polygon coordinates are array of rings, first ring is outer
            };

            await api.post('/regions/', {
                name: newRegion.name,
                type: newRegion.type,
                geometry: geometry
            });
            setNewRegion({ name: '', type: 'aoi', coordinates: '' });
            setShowCreateForm(false);
            fetchRegions();
            success('Region created successfully');
        } catch (err) {
            console.error(err);
            const errorMsg = err.response?.data?.detail || 'Failed to create region. Ensure coordinates are valid JSON array (e.g. [[28,42],[29,42],...]).';
            setError(errorMsg);
            showError(errorMsg);
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('Are you sure you want to delete this region?')) return;
        try {
            await api.delete(`/regions/${id}`);
            setRegions(regions.filter(r => r.id !== id));
            if (editingRegion?.id === id) {
                setEditingRegion(null);
            }
            success('Region deleted successfully');
        } catch (err) {
            console.error(err);
            const errorMsg = 'Failed to delete region: ' + (err.response?.data?.detail || err.message);
            showError(errorMsg);
        }
    };

    const handleEdit = (region) => {
        setEditingRegion(region);
        setEditForm({
            name: region.name,
            type: region.type || 'aoi',
            coordinates: '' // Geometry editing would require map interaction
        });
        setError('');
    };

    const handleCancelEdit = () => {
        setEditingRegion(null);
        setEditForm({ name: '', type: 'aoi', coordinates: '' });
        setError('');
    };

    const handleUpdate = async (e) => {
        e.preventDefault();
        if (!editingRegion) return;
        
        setError('');
        try {
            const updateData = {
                name: editForm.name,
                type: editForm.type
            };
            
            // Only include geometry if coordinates are provided
            if (editForm.coordinates) {
                try {
                    const coords = JSON.parse(editForm.coordinates);
                    updateData.geometry = {
                        type: "Polygon",
                        coordinates: [coords]
                    };
                } catch (parseError) {
                    setError('Invalid coordinates format. Use JSON array format: [[x,y],[x,y],...]');
                    return;
                }
            }

            await api.put(`/regions/${editingRegion.id}`, updateData);
            fetchRegions();
            handleCancelEdit();
            success('Region updated successfully');
        } catch (err) {
            console.error(err);
            const errorMsg = 'Failed to update region: ' + (err.response?.data?.detail || err.message);
            setError(errorMsg);
            showError(errorMsg);
        }
    };

    return (
        <div className="p-8 h-full overflow-y-auto">
            <div className="flex items-center justify-between mb-8">
                <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                    <MapPin className="w-8 h-8 text-blue-400" />
                    Regions Management
                </h1>
                <button
                    onClick={() => setShowCreateForm(!showCreateForm)}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors font-medium"
                >
                    <Plus className="w-5 h-5" />
                    {showCreateForm ? 'Cancel' : 'Add New Region'}
                </button>
            </div>

            {/* Create Region Form */}
            {showCreateForm && (
                <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 mb-8">
                    <h2 className="text-xl font-semibold text-blue-400 mb-4 flex items-center gap-2">
                        <Plus className="w-5 h-5" /> Add New Region
                    </h2>
                    {error && <p className="text-red-400 mb-4 p-3 bg-red-900/20 rounded border border-red-500/30">{error}</p>}
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
                            required
                        />
                        <button type="submit" className="bg-blue-600 text-white rounded p-2 font-semibold hover:bg-blue-700 transition flex items-center justify-center gap-2">
                            <Plus className="w-4 h-4" />
                            Create Region
                        </button>
                    </form>
                </div>
            )}

            {/* Regions List */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {loading ? (
                    <p className="text-gray-400">Loading regions...</p>
                ) : regions.length === 0 ? (
                    <p className="text-gray-500 italic">No regions found.</p>
                ) : (
                    regions.map(region => (
                        <div key={region.id} className="bg-gray-800 rounded-lg border border-gray-700 p-5 hover:border-blue-500/50 transition relative group">
                            {editingRegion?.id === region.id ? (
                                // Edit Form
                                <form onSubmit={handleUpdate} className="space-y-4">
                                    {error && <p className="text-red-400 text-sm">{error}</p>}
                                    <input
                                        type="text"
                                        placeholder="Region Name"
                                        className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:border-blue-500 outline-none"
                                        value={editForm.name}
                                        onChange={e => setEditForm({ ...editForm, name: e.target.value })}
                                        required
                                    />
                                    <select
                                        className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:border-blue-500 outline-none"
                                        value={editForm.type}
                                        onChange={e => setEditForm({ ...editForm, type: e.target.value })}
                                    >
                                        <option value="aoi">AOI</option>
                                        <option value="exclusion">Exclusion Zone</option>
                                    </select>
                                    <input
                                        type="text"
                                        placeholder='New Coordinates (optional)'
                                        className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:border-blue-500 outline-none text-sm"
                                        value={editForm.coordinates}
                                        onChange={e => setEditForm({ ...editForm, coordinates: e.target.value })}
                                    />
                                    <div className="flex gap-2">
                                        <button
                                            type="submit"
                                            className="flex-1 bg-green-600 hover:bg-green-700 text-white rounded p-2 font-semibold transition flex items-center justify-center gap-2"
                                        >
                                            <Save className="w-4 h-4" />
                                            Save
                                        </button>
                                        <button
                                            type="button"
                                            onClick={handleCancelEdit}
                                            className="bg-gray-700 hover:bg-gray-600 text-white rounded p-2 font-semibold transition flex items-center justify-center gap-2"
                                        >
                                            <X className="w-4 h-4" />
                                        </button>
                                    </div>
                                </form>
                            ) : (
                                // Display Mode
                                <>
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

                                    {region.description && (
                                        <p className="text-gray-400 text-sm mb-4">{region.description}</p>
                                    )}

                                    {region.area_km2 && (
                                        <p className="text-gray-500 text-xs mb-4">Area: {region.area_km2.toFixed(2)} km²</p>
                                    )}

                                    <div className="flex gap-2 mt-4">
                                        <button
                                            onClick={() => handleEdit(region)}
                                            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white rounded p-2 font-semibold transition flex items-center justify-center gap-2 text-sm"
                                        >
                                            <Edit2 className="w-4 h-4" />
                                            Edit
                                        </button>
                                        <button
                                            onClick={() => handleDelete(region.id)}
                                            className="bg-red-600 hover:bg-red-700 text-white rounded p-2 font-semibold transition flex items-center justify-center gap-2 text-sm"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
