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

export default function Dashboard() {
    const [dateRange, setDateRange] = useState('Last 30 Days');

    return (
        <div className="flex h-full flex-col space-y-4">
            <div className="flex items-center justify-between space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">Monitoring Map</h2>
                <div className="flex items-center space-x-2">
                    <Button variant="outline" className="hidden sm:flex">
                        <Calendar className="mr-2 h-4 w-4" />
                        {dateRange}
                    </Button>
                    <Button>Download Report</Button>
                </div>
            </div>

            <div className="grid h-full grid-cols-1 gap-4 lg:grid-cols-4">
                {/* Sidebar / Stats Panel */}
                <div className="space-y-4 lg:col-span-1">
                    <Card>
                        <CardHeader>
                            <CardTitle>Scene Filters</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Cloud Coverage</label>
                                <div className="flex items-center gap-2">
                                    <input type="range" className="w-full" min="0" max="100" defaultValue="10" />
                                    <span className="text-sm text-gray-500">10%</span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Recent Alerts</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-sm text-muted-foreground">No recent alerts.</div>
                        </CardContent>
                    </Card>
                </div>

                {/* Main Map Area */}
                <div className="lg:col-span-3 h-[500px] lg:h-auto">
                    <Card className="h-full">
                        <CardContent className="p-0 h-full">
                            <AppMap regions={MOCK_REGIONS as any} />
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
