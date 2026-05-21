import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';
import api from '@/api/axios';
import { Scene } from '@/api/types';

interface SceneAnalysisProps {
    scene: Scene;
}

export function SceneAnalysis({ scene }: SceneAnalysisProps) {
    const [loading, setLoading] = useState(false);
    const [stats, setStats] = useState({
        total_vegetation_area_m2: 0,
        vegetation_trend_percent: 0,
        avg_confidence: 0,
        confidence_trend_percent: 0,
        active_anomalies: 0,
        anomalies_trend: 0
    });

    useEffect(() => {
        if (!scene) return;
        const fetchStats = async () => {
            setLoading(true);
            try {
                const response = await api.get('/analysis/stats', {
                    params: { scene_id: scene.id }
                });
                setStats(response.data);
            } catch (error) {
                console.error('Failed to fetch scene stats:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, [scene]);

    if (loading) {
        return (
            <div className="flex h-32 items-center justify-center col-span-full">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="grid gap-4 md:grid-cols-3">
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Vegetation Area</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{(stats.total_vegetation_area_m2 / 1_000_000).toLocaleString(undefined, { maximumFractionDigits: 2 })} km²</div>
                    <p className="text-xs text-muted-foreground">
                        {stats.vegetation_trend_percent > 0 ? '+' : ''}{stats.vegetation_trend_percent}% from previous scene
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
                        {stats.confidence_trend_percent > 0 ? '+' : ''}{stats.confidence_trend_percent}% from previous scene
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
    );
}
