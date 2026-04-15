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
    const [dateRangeFilter, setDateRangeFilter] = useState<'All Time' | 'Last 30 Days'>('All Time');
    const [cloudCover, setCloudCover] = useState([10]);
    const [selectedScene, setSelectedScene] = useState<Scene | null>(null);
    const [regions, setRegions] = useState<Region[]>([]);
    const [scenes, setScenes] = useState<Scene[]>([]);
    const [dateAfter, setDateAfter] = useState<string>('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                console.log('Fetching from /scenes...');
                const [regionsRes, scenesRes] = await Promise.all([
                    api.get<Region[]>('/regions?with_geometry=true'),
                    api.get<Scene[]>('/scenes')
                ]);
                console.log('Fetched scenes data:', scenesRes.data);
                setRegions(regionsRes.data);
                setScenes(scenesRes.data);
            } catch (error: any) {
                console.error('Failed to fetch data:', error);
                if (error.response) {
                    console.error('Response data:', error.response.data);
                    console.error('Response status:', error.response.status);
                }
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    useEffect(() => {
        if (!selectedScene && scenes.length > 0) {
            // Auto-select the first scene once loaded
            const firstFiltered = scenes.filter((s: Scene) => {
                const matchesCloud = (s.cloud_cover ?? 0) <= cloudCover[0];
                const matchesDate = !dateAfter || new Date(s.acquisition_date) >= new Date(dateAfter);
                return matchesCloud && matchesDate;
            })[0];
            if (firstFiltered) setSelectedScene(firstFiltered);
        }
    }, [scenes, cloudCover, dateAfter, selectedScene]);

    const filteredScenes = scenes.filter((s: Scene) => {
        const matchesCloud = (s.cloud_cover ?? 0) <= cloudCover[0];
        const matchesDate = !dateAfter || new Date(s.acquisition_date) >= new Date(dateAfter);
        return matchesCloud && matchesDate;
    }).sort((a, b) => new Date(b.acquisition_date).getTime() - new Date(a.acquisition_date).getTime());

    console.log('Filtered scenes count:', filteredScenes.length);
    if (filteredScenes.length === 0 && scenes.length > 0) {
        console.log('Filter mismatch details:', {
            firstSceneCloud: scenes[0].cloud_cover,
            filterCloud: cloudCover[0],
            firstSceneDate: scenes[0].acquisition_date,
            filterDateAfter: dateAfter
        });
    }

    const toggleDateFilter = () => {
        if (dateRangeFilter === 'All Time') {
            const date = new Date();
            date.setDate(date.getDate() - 30);
            setDateAfter(date.toISOString().split('T')[0]);
            setDateRangeFilter('Last 30 Days');
        } else {
            setDateAfter('');
            setDateRangeFilter('All Time');
        }
    };

    const downloadReportCSV = () => {
        const headers = ["Scene ID", "Acquisition Date", "Cloud Cover (%)", "Region ID", "Status"];
        const rows = filteredScenes.map(s => [
            s.scene_id,
            s.acquisition_date,
            s.cloud_cover !== null && s.cloud_cover !== undefined ? s.cloud_cover.toFixed(2) : "N/A",
            s.region_id,
            "Analyzed"
        ]);
        
        const csvContent = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `monitoring_report_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

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
                    <Button variant={dateRangeFilter === 'All Time' ? 'outline' : 'default'} className="hidden sm:flex" size="sm" onClick={toggleDateFilter}>
                        <Calendar className="mr-2 h-4 w-4" />
                        {dateRangeFilter === 'All Time' ? 'Filter: Last 30 Days' : 'Clear: Last 30 Days'}
                    </Button>
                    <Button size="sm" onClick={downloadReportCSV}>Download Report</Button>
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
                                Available Scenes ({filteredScenes.length})
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="flex flex-col max-h-[400px] overflow-y-auto">
                                {filteredScenes.length === 0 ? (
                                    <div className="p-8 text-xs text-muted-foreground text-center flex flex-col items-center gap-2">
                                        <Layers className="h-8 w-8 opacity-20" />
                                        {scenes.length > 0 ? (
                                            <div className="flex flex-col gap-1">
                                                <p className="font-semibold text-foreground">Filtered out</p>
                                                <p>Adjust cloud/date filters to see {scenes.length} available scenes.</p>
                                            </div>
                                        ) : 'No scenes available for this region.'}
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
                                                <span className="text-xs font-mono font-bold truncate">{scene.scene_id}</span>
                                                <div className="flex items-center justify-between">
                                                    <span className="text-[10px] text-muted-foreground">
                                                        {scene.acquisition_date}
                                                    </span>
                                                    <Badge variant="outline" className="text-[9px] h-4">
                                                        {scene.cloud_cover !== null && scene.cloud_cover !== undefined
                                                            ? `${scene.cloud_cover.toFixed(1)}% cloud`
                                                            : 'Manual'}
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
                                selectedSceneUrl={selectedScene ? `${import.meta.env.VITE_API_URL}/data/inference/${selectedScene.scene_id}_classification.tif` : undefined}
                            />
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
