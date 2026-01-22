import { useEffect, useState } from 'react';
import AppMap from '../components/Map/Map';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar, Loader2, Layers, Image as ImageIcon } from 'lucide-react';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Region, Scene } from '../api/types';
import api from '@/api/axios';

// Mock Data replaced by API calls in useEffect

export default function Dashboard() {
    const dateRange = 'Last 30 Days';
    const [cloudCover, setCloudCover] = useState([10]);
    const [selectedScene, setSelectedScene] = useState<Scene | null>(null);
    const [regions, setRegions] = useState<Region[]>([]);
    const [scenes, setScenes] = useState<Scene[]>([]);
    const [dateAfter, setDateAfter] = useState<string>('2023-01-01');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const [regionsRes, scenesRes] = await Promise.all([
                    api.get<Region[]>('/regions?with_geometry=true'),
                    api.get<Scene[]>('/scenes')
                ]);
                setRegions(regionsRes.data);
                setScenes(scenesRes.data);
            } catch (error) {
                console.error('Failed to fetch data:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const filteredScenes = scenes.filter((s: Scene) => {
        const matchesCloud = s.cloud_coverage <= cloudCover[0];
        const matchesDate = !dateAfter || new Date(s.acquired_at) >= new Date(dateAfter);
        return matchesCloud && matchesDate;
    });

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="flex h-full flex-col space-y-4">
            <div className="flex items-center justify-between space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">Monitoring Map</h2>
                <div className="flex items-center space-x-2">
                    <Button variant="outline" className="hidden sm:flex" size="sm">
                        <Calendar className="mr-2 h-4 w-4" />
                        {dateRange}
                    </Button>
                    <Button size="sm" onClick={() => alert('Generating PDF report for the current view...')}>Download Report</Button>
                </div>
            </div>

            <div className="grid h-full grid-cols-1 gap-4 lg:grid-cols-4">
                {/* Sidebar / Stats Panel */}
                <div className="space-y-4 lg:col-span-1 overflow-y-auto pr-1">
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-lg flex items-center gap-2">
                                <Layers className="h-4 w-4" />
                                Scene Filters
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-3">
                                <div className="flex justify-between">
                                    <label className="text-sm font-medium">Cloud Coverage</label>
                                    <span className="text-xs font-mono bg-muted px-1 rounded">{cloudCover[0]}%</span>
                                </div>
                                <Slider
                                    value={cloudCover}
                                    onValueChange={setCloudCover}
                                    max={100}
                                    step={1}
                                />
                            </div>
                            <div className="space-y-3 pt-2">
                                <label className="text-sm font-medium">Date After</label>
                                <input
                                    type="date"
                                    className="w-full flex h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                                    onChange={(e) => setDateAfter(e.target.value)}
                                    value={dateAfter}
                                />
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-lg flex items-center gap-2">
                                <ImageIcon className="h-4 w-4" />
                                Available Scenes
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="flex flex-col">
                                {filteredScenes.length === 0 ? (
                                    <div className="p-4 text-xs text-muted-foreground text-center">
                                        No scenes match the filter.
                                    </div>
                                ) : (
                                    filteredScenes.map(scene => (
                                        <div
                                            key={scene.id}
                                            onClick={() => setSelectedScene(scene)}
                                            className={`p-3 border-b last:border-0 cursor-pointer hover:bg-muted/50 transition-colors ${selectedScene?.id === scene.id ? 'bg-primary/5 border-l-4 border-l-primary' : ''
                                                }`}
                                        >
                                            <div className="flex flex-col gap-1">
                                                <span className="text-xs font-mono font-bold truncate">{scene.sentinel_id}</span>
                                                <div className="flex items-center justify-between">
                                                    <span className="text-[10px] text-muted-foreground">{new Date(scene.acquired_at).toLocaleDateString()}</span>
                                                    <Badge variant="outline" className="text-[9px] h-4">
                                                        {scene.cloud_coverage}% cloud
                                                    </Badge>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-lg">Recent Alerts</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-xs text-muted-foreground">No recent alerts.</div>
                        </CardContent>
                    </Card>
                </div>

                {/* Main Map Area */}
                <div className="lg:col-span-3 h-[600px] lg:h-auto">
                    <Card className="h-full">
                        <CardContent className="p-0 h-full">
                            <AppMap
                                regions={regions}
                                selectedSceneUrl={selectedScene ? `${import.meta.env.VITE_API_URL}/data/inference/${selectedScene.sentinel_id}_classification.tif` : undefined}
                            />
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
