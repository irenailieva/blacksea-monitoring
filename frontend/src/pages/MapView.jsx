import { useState, useEffect } from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import RasterLayer from '../components/Map/RasterLayer';
import RegionsLayer from '../components/Map/RegionsLayer';
import api from '../lib/api';
import { Filter, Layers, MapPin, Calendar, Satellite } from 'lucide-react';

export default function MapView() {
    const [scenes, setScenes] = useState([]);
    const [regions, setRegions] = useState([]);
    const [regionsWithGeometry, setRegionsWithGeometry] = useState([]);
    const [selectedScene, setSelectedScene] = useState(null);
    const [selectedRegion, setSelectedRegion] = useState(null);
    const [loading, setLoading] = useState(true);
    const [regionsLoading, setRegionsLoading] = useState(true);
    const [showRegions, setShowRegions] = useState(true);

    // Default to Black Sea (rough coords)
    const position = [43.0, 30.0];

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [scenesRes, regionsRes, regionsGeoRes] = await Promise.all([
                    api.get('/scenes/'),
                    api.get('/regions/'),
                    api.get('/regions/', { params: { with_geometry: true } }).catch(() => ({ data: [] }))
                ]);
                setScenes(scenesRes.data);
                setRegions(regionsRes.data);
                setRegionsWithGeometry(regionsGeoRes.data || []);
            } catch (error) {
                console.error("Failed to fetch data:", error);
            } finally {
                setLoading(false);
                setRegionsLoading(false);
            }
        };
        fetchData();
    }, []);

    // Filter scenes by selected region
    const filteredScenes = selectedRegion
        ? scenes.filter(scene => scene.region_id === selectedRegion.id)
        : scenes;

    return (
        <div className="flex h-full">
            {/* Map Area */}
            <div className="flex-1 relative z-0">
                <MapContainer center={position} zoom={8} style={{ height: '100%', width: '100%' }}>
                    <TileLayer
                        attribution='&copy; OpenStreetMap contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />

                    {selectedScene && (
                        <RasterLayer
                            url={`http://localhost:8000/data/inference/${selectedScene.scene_id}_classification.tif`}
                        />
                    )}
                    {showRegions && (
                        <RegionsLayer regions={regionsWithGeometry} visible={showRegions} />
                    )}
                </MapContainer>
            </div>

            {/* Control Panel */}
            <div className="w-96 bg-gray-800 border-l border-gray-700 flex flex-col z-10">
                {/* Header */}
                <div className="p-4 border-b border-gray-700">
                    <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <Layers className="w-5 h-5" />
                        Map Controls
                    </h2>

                    {/* Region Filter */}
                    <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-400 mb-2 flex items-center gap-2">
                            <Filter className="w-4 h-4" />
                            Filter by Region
                        </label>
                        <select
                            className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:border-blue-500 outline-none text-sm"
                            value={selectedRegion?.id || ''}
                            onChange={(e) => {
                                const regionId = parseInt(e.target.value);
                                setSelectedRegion(regions.find(r => r.id === regionId) || null);
                            }}
                        >
                            <option value="">All Regions</option>
                            {regions.map(region => (
                                <option key={region.id} value={region.id}>
                                    {region.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Toggle Regions Visibility */}
                    <button
                        onClick={() => setShowRegions(!showRegions)}
                        className={`w-full flex items-center gap-2 px-3 py-2 rounded text-sm font-medium transition ${
                            showRegions
                                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/50'
                                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                        }`}
                    >
                        <MapPin className="w-4 h-4" />
                        {showRegions ? 'Hide Regions' : 'Show Regions'}
                    </button>
                </div>

                {/* Scenes List */}
                <div className="flex-1 overflow-y-auto p-4">
                    <h3 className="text-md font-semibold text-white mb-3 flex items-center gap-2">
                        <Satellite className="w-4 h-4" />
                        Available Scenes
                        {selectedRegion && (
                            <span className="text-xs text-gray-400 ml-auto">
                                ({filteredScenes.length} of {scenes.length})
                            </span>
                        )}
                    </h3>

                    {loading ? (
                        <p className="text-gray-400 text-sm">Loading scenes...</p>
                    ) : filteredScenes.length === 0 ? (
                        <p className="text-gray-500 text-sm">
                            {selectedRegion ? 'No scenes found for selected region.' : 'No scenes found.'}
                        </p>
                    ) : (
                        <div className="space-y-2">
                            {filteredScenes.map((scene) => (
                                <div
                                    key={scene.id}
                                    onClick={() => setSelectedScene(scene)}
                                    className={`p-3 rounded cursor-pointer transition border ${
                                        selectedScene?.id === scene.id
                                            ? 'bg-blue-600/20 border-blue-500'
                                            : 'bg-gray-700 hover:bg-gray-600 border-gray-600'
                                    }`}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="text-sm font-medium text-white">{scene.scene_id}</div>
                                            <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                                                <span className="flex items-center gap-1">
                                                    <Calendar className="w-3 h-3" />
                                                    {new Date(scene.acquisition_date).toLocaleDateString()}
                                                </span>
                                                {scene.satellite && (
                                                    <span className="flex items-center gap-1">
                                                        <Satellite className="w-3 h-3" />
                                                        {scene.satellite}
                                                    </span>
                                                )}
                                            </div>
                                            {scene.cloud_cover !== null && (
                                                <div className="text-xs text-gray-500 mt-1">
                                                    Cloud cover: {scene.cloud_cover.toFixed(1)}%
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Selected Scene Info */}
                {selectedScene && (
                    <div className="p-4 border-t border-gray-700 bg-gray-900/50">
                        <h4 className="text-sm font-semibold text-blue-400 mb-2">Selected Scene</h4>
                        <div className="text-xs text-gray-300 space-y-1">
                            <div><strong>ID:</strong> {selectedScene.scene_id}</div>
                            <div><strong>Date:</strong> {new Date(selectedScene.acquisition_date).toLocaleDateString()}</div>
                            {selectedScene.region_id && (
                                <div>
                                    <strong>Region:</strong> {regions.find(r => r.id === selectedScene.region_id)?.name || 'Unknown'}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
