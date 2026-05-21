import { useEffect, useState } from 'react';
import { VegetationChart } from '@/components/Analysis/VegetationChart';
import { ShapExplanation } from '@/components/Analysis/ShapExplanation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from '@/components/ui/button';
import { Download, Loader2 } from 'lucide-react';
import api from '@/api/axios';
import { Region } from '@/api/types';

export default function Analysis() {
    const [selectedRegion, setSelectedRegion] = useState<string>('');
    const [regions, setRegions] = useState<Region[]>([]);
    const [loading, setLoading] = useState(true);
    
    const [stats, setStats] = useState({
        total_vegetation_area_m2: 0,
        vegetation_trend_percent: 0,
        avg_confidence: 0,
        confidence_trend_percent: 0,
        active_anomalies: 0,
        anomalies_trend: 0
    });

    useEffect(() => {
        const fetchRegions = async () => {
            try {
                const response = await api.get<Region[]>('/regions');
                const filteredRegions = response.data.filter(r => !r.name.startsWith('AOI_'));
                setRegions(filteredRegions);
                if (filteredRegions.length > 0) {
                    setSelectedRegion(filteredRegions[0].id.toString());
                }
            } catch (error) {
                console.error('Failed to fetch regions:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchRegions();
    }, []);

    useEffect(() => {
        if (!selectedRegion) return;
        const fetchStats = async () => {
            try {
                const response = await api.get('/analysis/stats', {
                    params: { region_id: selectedRegion }
                });
                setStats(response.data);
            } catch (error) {
                console.error('Failed to fetch stats:', error);
            }
        };
        fetchStats();
    }, [selectedRegion]);

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    const exportAnalysisCSV = () => {
        const regionName = regions.find(r => r.id.toString() === selectedRegion)?.name || 'Unknown Region';
        const headers = ["Region", "Metric", "Value", "Trend"];
        const rows = [
            [regionName, "Total Vegetation Area (km²)", (stats.total_vegetation_area_m2 / 1_000_000).toFixed(2), `${stats.vegetation_trend_percent > 0 ? '+' : ''}${stats.vegetation_trend_percent}%`],
            [regionName, "Average Confidence Score (%)", stats.avg_confidence.toString(), `${stats.confidence_trend_percent > 0 ? '+' : ''}${stats.confidence_trend_percent}%`],
            [regionName, "Active Anomalies", stats.active_anomalies.toString(), `${stats.anomalies_trend > 0 ? '+' : ''}${stats.anomalies_trend}`]
        ];
        
        const csvContent = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `analysis_summary_${regionName.replace(/ /g, '_')}_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div className="flex flex-col space-y-4 h-full  overflow-y-auto pr-2">
            <div className="flex items-center justify-between space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">Analysis Dashboard</h2>
                <div className="flex items-center space-x-2">
                    <Select value={selectedRegion} onValueChange={setSelectedRegion}>
                        <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder="Select Region" />
                        </SelectTrigger>
                        <SelectContent>
                            {regions.map(region => (
                                <SelectItem key={region.id} value={region.id.toString()}>
                                    {region.name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                    <Button size="icon" variant="outline" onClick={exportAnalysisCSV}>
                        <Download className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Vegetation Area</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{(stats.total_vegetation_area_m2 / 1_000_000).toLocaleString(undefined, { maximumFractionDigits: 2 })} km²</div>
                        <p className="text-xs text-muted-foreground">
                            {stats.vegetation_trend_percent > 0 ? '+' : ''}{stats.vegetation_trend_percent}% from last scene
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avg. Confidence Score</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.avg_confidence}%</div>
                        <p className="text-xs text-muted-foreground">
                            {stats.confidence_trend_percent > 0 ? '+' : ''}{stats.confidence_trend_percent}% from last scene
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Active Anomalies</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.active_anomalies}</div>
                        <p className="text-xs text-muted-foreground">
                            {stats.anomalies_trend > 0 ? '+' : ''}{stats.anomalies_trend} new anomalies
                        </p>
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-3">
                <VegetationChart regionId={selectedRegion ? Number(selectedRegion) : null} />
                <ShapExplanation regionId={selectedRegion} />
            </div>

            <div className="grid gap-4 md:grid-cols-1">
                <Card>
                    <CardHeader>
                        <CardTitle>Detailed Report</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="rounded-md border p-4 text-sm text-center text-muted-foreground bg-muted/20">
                            Table of specific classification results per scene will go here.
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
