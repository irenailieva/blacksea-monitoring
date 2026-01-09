import { useState } from 'react';
import AppMap from '../components/Map/Map';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar } from 'lucide-react';
// import { Region } from '../api/types';

// Mock Data for now
const MOCK_REGIONS = [
    {
        id: 1,
        name: 'Varna Bay',
        type: 'aoi',
        geometry: {
            type: 'Polygon',
            coordinates: [
                [
                    [27.88, 43.18],
                    [27.95, 43.18],
                    [27.95, 43.22],
                    [27.88, 43.22],
                    [27.88, 43.18]
                ]
            ]
        }
    },
    {
        id: 2,
        name: 'Burgas Bay',
        type: 'aoi',
        geometry: {
            type: 'Polygon',
            coordinates: [
                [
                    [27.45, 42.45],
                    [27.55, 42.45],
                    [27.55, 42.55],
                    [27.45, 42.55],
                    [27.45, 42.45]
                ]
            ]
        }
    }
];

import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Layers, Image as ImageIcon } from 'lucide-react';

// Mock Scenes
const MOCK_SCENES = [
    { id: 1, scene_id: 'S2A_MSIL2A_20230715', acquisition_date: '2023-07-15', cloud_cover: 2.1, url: 'http://localhost:8000/data/inference/scene_1_classification.tif' },
    { id: 2, scene_id: 'S2B_MSIL2A_20230720', acquisition_date: '2023-07-20', cloud_cover: 8.5, url: 'http://localhost:8000/data/inference/scene_2_classification.tif' },
];

export default function Dashboard() {
    const [dateRange, setDateRange] = useState('Last 30 Days');
    const [cloudCover, setCloudCover] = useState([10]);
    const [selectedScene, setSelectedScene] = useState<typeof MOCK_SCENES[0] | null>(null);

    const filteredScenes = MOCK_SCENES.filter(s => s.cloud_cover <= cloudCover[0]);

    return (
        <div className="flex h-full flex-col space-y-4">
            <div className="flex items-center justify-between space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">Monitoring Map</h2>
                <div className="flex items-center space-x-2">
                    <Button variant="outline" className="hidden sm:flex" size="sm">
                        <Calendar className="mr-2 h-4 w-4" />
                        {dateRange}
                    </Button>
                    <Button size="sm">Download Report</Button>
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
                                                <span className="text-xs font-mono font-bold truncate">{scene.scene_id}</span>
                                                <div className="flex items-center justify-between">
                                                    <span className="text-[10px] text-muted-foreground">{scene.acquisition_date}</span>
                                                    <Badge variant="outline" className="text-[9px] h-4">
                                                        {scene.cloud_cover}% cloud
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
                                regions={MOCK_REGIONS as any}
                                selectedSceneUrl={selectedScene?.url}
                            />
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
