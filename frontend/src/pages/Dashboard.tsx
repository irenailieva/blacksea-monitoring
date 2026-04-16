import { useEffect, useState, useCallback } from 'react';
import AppMap from '../components/Map/Map';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, Layers, Image as ImageIcon, RefreshCw, CheckCircle2, AlertCircle, Clock, Satellite } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Region, Scene } from '../api/types';
import api from '@/api/axios';
import { BBox } from '@/components/Map/AoiDrawTool';

// ── types ──────────────────────────────────────────────────────────────────────
interface ActiveJob {
    job_id: number;
    aoi_name: string;
    bbox: BBox;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    scene_id_str?: string;
}

// ── component ──────────────────────────────────────────────────────────────────
export default function Dashboard() {
    const [regions, setRegions] = useState<Region[]>([]);
    const [scenes, setScenes] = useState<Scene[]>([]);
    const [selectedScene, setSelectedScene] = useState<Scene | null>(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [activeJob, setActiveJob] = useState<ActiveJob | null>(null);

    // ── data init ────────────────────────────────────────────────────────────
    useEffect(() => {
        const init = async () => {
            setLoading(true);
            try {
                const [regionsRes, scenesRes] = await Promise.all([
                    api.get<Region[]>('/regions?with_geometry=true'),
                    api.get<Scene[]>('/scenes'),
                ]);
                setRegions(regionsRes.data);
                setScenes(scenesRes.data);
                if (scenesRes.data.length > 0) setSelectedScene(scenesRes.data[scenesRes.data.length - 1]);
            } catch (e) {
                console.error('Failed to load initial data:', e);
            } finally {
                setLoading(false);
            }
        };
        init();
    }, []);

    // ── scene refresh ────────────────────────────────────────────────────────
    const fetchScenes = useCallback(async (silent = false) => {
        if (!silent) setRefreshing(true);
        try {
            const res = await api.get<Scene[]>('/scenes');
            setScenes(res.data);
        } catch (e) {
            console.error('Scene refresh failed:', e);
        } finally {
            setRefreshing(false);
        }
    }, []);

    // ── job polling ──────────────────────────────────────────────────────────
    useEffect(() => {
        if (!activeJob || activeJob.status === 'completed' || activeJob.status === 'failed') return;

        const interval = setInterval(async () => {
            try {
                const res = await api.get('/scenes/etl-status');
                const jobs: any[] = res.data;
                const job = jobs.find(j => j.id === activeJob.job_id);
                if (!job) return;

                const progress = job.payload?.progress ?? activeJob.progress;
                const scene_id_str = job.payload?.scene_id_str ?? activeJob.scene_id_str;

                setActiveJob(prev => prev ? {
                    ...prev,
                    status: job.status,
                    progress,
                    scene_id_str,
                } : null);

                if (job.status === 'completed') {
                    clearInterval(interval);
                    await fetchScenes(true);
                    // Auto-select the newly processed scene
                    const newRes = await api.get<Scene[]>('/scenes');
                    const allScenes = newRes.data;
                    setScenes(allScenes);
                    // Find scene matching the aoi_name or pick latest
                    const newest = allScenes[allScenes.length - 1];
                    if (newest) setSelectedScene(newest);
                }
                if (job.status === 'failed') clearInterval(interval);
            } catch {/* silent */}
        }, 3000);

        return () => clearInterval(interval);
    }, [activeJob, fetchScenes]);

    // Auto-refresh scenes every 30 s (passive background)
    useEffect(() => {
        const iv = setInterval(() => fetchScenes(true), 30_000);
        return () => clearInterval(iv);
    }, [fetchScenes]);

    // ── AOI submit ───────────────────────────────────────────────────────────
    const handleAoiSubmit = useCallback(async (bbox: BBox, aoi_name: string) => {
        try {
            const res = await api.post('/scenes/analyze-aoi', {
                bbox,
                aoi_name,
                cloud_max: 30,
            });
            setActiveJob({
                job_id: res.data.job_id,
                aoi_name,
                bbox,
                status: 'pending',
                progress: 0,
            });
        } catch (e: any) {
            console.error('AOI analysis failed to start:', e);
            alert(e?.response?.data?.detail ?? 'Failed to start analysis. Check your role permissions.');
        }
    }, []);

    // ── derived ──────────────────────────────────────────────────────────────
    const sortedScenes = [...scenes].sort(
        (a, b) => new Date(b.acquisition_date).getTime() - new Date(a.acquisition_date).getTime()
    );

    const selectedSceneUrl = selectedScene
        ? `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/data/inference/${selectedScene.scene_id}_classification.tif`
        : undefined;

    // ── render ───────────────────────────────────────────────────────────────
    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="flex h-full flex-col space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Monitoring Map</h2>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Satellite className="h-3.5 w-3.5" />
                    Draw an area on the map to start analysis
                </div>
            </div>

            <div className="grid h-full grid-cols-1 gap-4 lg:grid-cols-4">
                {/* ── Sidebar ── */}
                <div className="space-y-4 lg:col-span-1 overflow-y-auto pr-1">

                    {/* Active job status card */}
                    {activeJob && (
                        <Card className={`border-2 ${
                            activeJob.status === 'failed' ? 'border-destructive/40' :
                            activeJob.status === 'completed' ? 'border-green-500/40' :
                            'border-primary/40'
                        }`}>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm flex items-center gap-2">
                                    {activeJob.status === 'completed' && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                                    {activeJob.status === 'failed' && <AlertCircle className="h-4 w-4 text-destructive" />}
                                    {(activeJob.status === 'pending' || activeJob.status === 'processing') && (
                                        <Loader2 className="h-4 w-4 animate-spin text-primary" />
                                    )}
                                    AOI Analysis
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2">
                                <p className="text-[11px] font-mono truncate text-muted-foreground">{activeJob.aoi_name}</p>
                                <p className="text-[10px] text-muted-foreground">
                                    [{activeJob.bbox.map(v => v.toFixed(3)).join(', ')}]
                                </p>
                                <Progress
                                    value={activeJob.status === 'completed' ? 100 : activeJob.progress}
                                    className="h-1.5"
                                />
                                <div className="flex items-center justify-between">
                                    <Badge
                                        variant={activeJob.status === 'completed' ? 'default' : activeJob.status === 'failed' ? 'destructive' : 'secondary'}
                                        className="text-[10px] uppercase"
                                    >
                                        {activeJob.status === 'pending' ? (
                                            <><Clock className="h-2.5 w-2.5 mr-1" />Queued</>
                                        ) : activeJob.status}
                                    </Badge>
                                    <span className="text-[10px] text-muted-foreground">
                                        {activeJob.status === 'completed' ? 100 : activeJob.progress}%
                                    </span>
                                </div>
                                {activeJob.status === 'completed' && (
                                    <p className="text-[10px] text-green-600 font-medium">
                                        ✓ Classification loaded on map
                                    </p>
                                )}
                                {activeJob.status === 'failed' && (
                                    <p className="text-[10px] text-destructive">
                                        Pipeline failed — check ETL logs
                                    </p>
                                )}
                                {(activeJob.status === 'completed' || activeJob.status === 'failed') && (
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="w-full h-6 text-[10px]"
                                        onClick={() => setActiveJob(null)}
                                    >
                                        Dismiss
                                    </Button>
                                )}
                            </CardContent>
                        </Card>
                    )}

                    {/* Available scenes */}
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-lg flex items-center gap-2">
                                <ImageIcon className="h-4 w-4" />
                                Available Scenes ({sortedScenes.length})
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-5 w-5 ml-auto"
                                    onClick={() => fetchScenes()}
                                    disabled={refreshing}
                                    title="Refresh scenes"
                                >
                                    <RefreshCw className={`h-3 w-3 ${refreshing ? 'animate-spin' : ''}`} />
                                </Button>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="flex flex-col max-h-[360px] overflow-y-auto">
                                {sortedScenes.length === 0 ? (
                                    <div className="p-8 text-xs text-muted-foreground text-center flex flex-col items-center gap-2">
                                        <Layers className="h-8 w-8 opacity-20" />
                                        <p>No scenes yet.</p>
                                        <p className="text-[10px]">Draw an area on the map to trigger your first analysis.</p>
                                    </div>
                                ) : (
                                    sortedScenes.map(scene => (
                                        <div
                                            key={scene.id}
                                            onClick={() => setSelectedScene(scene)}
                                            className={`p-3 border-b last:border-0 cursor-pointer hover:bg-muted/50 transition-colors ${
                                                selectedScene?.id === scene.id
                                                    ? 'bg-primary/5 border-l-4 border-l-primary'
                                                    : ''
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

                    {/* Instructions card */}
                    <Card className="border-dashed">
                        <CardContent className="p-4 space-y-2">
                            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">How it works</p>
                            <ol className="text-[11px] text-muted-foreground space-y-1.5 list-decimal list-inside">
                                <li>Click <strong>"Analyze Area"</strong> on the map</li>
                                <li>Drag to draw your area of interest</li>
                                <li>Click <strong>"Analyze this area"</strong></li>
                                <li>Wait for the pipeline to complete</li>
                                <li>Classification overlay loads automatically</li>
                            </ol>
                        </CardContent>
                    </Card>
                </div>

                {/* ── Map ── */}
                <div className="lg:col-span-3 h-[600px] lg:h-auto">
                    <Card className="h-full">
                        <CardContent className="p-0 h-full">
                            <AppMap
                                regions={regions}
                                selectedSceneUrl={selectedSceneUrl}
                                onAoiSubmit={handleAoiSubmit}
                            />
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
