import { useState, useEffect } from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import RasterLayer from '../components/Map/RasterLayer';
import api from '../lib/api';

export default function MapView() {
    const [scenes, setScenes] = useState([]);
    const [selectedScene, setSelectedScene] = useState(null);
    const [loading, setLoading] = useState(true);

    // Default to Black Sea (rough coords)
    const position = [43.0, 30.0];

    useEffect(() => {
        const fetchScenes = async () => {
            try {
                // Fetch scenes (mocking endpoint success even if empty)
                const response = await api.get('/scenes/');
                setScenes(response.data);
            } catch (error) {
                console.error("Failed to fetch scenes:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchScenes();
    }, []);

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
                        // Assuming TIF URL structure from our implementation plan
                        // We need to fetch the file path. backend serves /data maps to /app/ml
                        // If db has /app/ml/data/inference/file.tif, we serve http://localhost:8000/data/inference/file.tif
                        <RasterLayer
                            url={`http://localhost:8000/data/inference/${selectedScene.scene_id}_classification.tif`}
                        />
                    )}

                </MapContainer>
            </div>

            {/* Control Panel */}
            <div className="w-80 bg-gray-800 border-l border-gray-700 p-4 overflow-y-auto z-10">
                <h2 className="text-lg font-bold text-white mb-4">Available Scenes</h2>

                {loading ? (
                    <p className="text-gray-400">Loading scenes...</p>
                ) : (
                    <div className="space-y-3">
                        {scenes.map((scene) => (
                            <div
                                key={scene.id}
                                onClick={() => setSelectedScene(scene)}
                                className={`p-3 rounded cursor-pointer transition ${selectedScene?.id === scene.id
                                        ? 'bg-blue-600/20 border border-blue-500'
                                        : 'bg-gray-700 hover:bg-gray-600'
                                    }`}
                            >
                                <div className="text-sm font-medium text-white">{scene.scene_id}</div>
                                <div className="text-xs text-gray-400 mt-1">
                                    {new Date(scene.acquisition_date).toLocaleDateString()}
                                </div>
                            </div>
                        ))}

                        {scenes.length === 0 && (
                            <p className="text-gray-500 text-sm">No scenes found.</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
