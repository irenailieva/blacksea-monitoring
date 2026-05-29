import { useEffect, useState, useCallback } from 'react';
import useAuth from '../store/useAuth';
import AppMap from '../components/Map/Map';
import { SceneAnalysis } from '@/components/Analysis/SceneAnalysis';
import { ShapExplanation } from '@/components/Analysis/ShapExplanation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Loader2, Layers, Image as ImageIcon, RefreshCw, CheckCircle2, AlertCircle, Clock, Satellite } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Region, Scene } from '../api/types';
import api from '@/api/axios';
import { BBox } from '@/components/Map/AoiDrawTool';

// ── Типове (Types) ──────────────────────────────────────────────────────────────────────
// Интерфейс, описващ активна фонова задача (напр. заявка за анализ на нова зона)
interface ActiveJob {
    job_id: number;
    aoi_name: string;
    bbox: BBox;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    scene_id_str?: string;
}

// ── Главен Компонент (Component) ──────────────────────────────────────────────────────────────────
// Страница "Табло за управление" (Dashboard), която съдържа основната карта и страничната лента със сцени
export default function Dashboard() {
    const { user } = useAuth(); // Вземане на текущия потребител от глобалното състояние (Zustand)
    // Проверка на правата за достъп (само изследователи и администратори могат да стартират нов анализ)
    const canAnalyze = user?.role === 'researcher' || user?.role === 'admin';
    
    // Локални състояния (State)
    const [regions, setRegions] = useState<Region[]>([]); // Запазени географски региони
    const [scenes, setScenes] = useState<Scene[]>([]); // Списък с обработените сателитни сцени
    const [selectedScene, setSelectedScene] = useState<Scene | null>(null); // Текущо избрана сцена за визуализация
    const [loading, setLoading] = useState(true); // Флаг за първоначално зареждане
    const [refreshing, setRefreshing] = useState(false); // Флаг за ръчно опресняване на сцените
    const [activeJob, setActiveJob] = useState<ActiveJob | null>(null); // Информация за текущо изпълнявана фонова задача
    const [activeTab, setActiveTab] = useState("map"); // Избран таб (Карта или Анализ)

    // ── Инициализация на данните (Data Init) ────────────────────────────────────────────────────────────
    useEffect(() => {
        const init = async () => {
            setLoading(true);
            try {
                // Паралелно извличане на регионите (заедно с геометрията) и сцените от API-то
                const [regionsRes, scenesRes] = await Promise.all([
                    api.get<Region[]>('/regions?with_geometry=true'),
                    api.get<Scene[]>('/scenes'),
                ]);
                setRegions(regionsRes.data);
                setScenes(scenesRes.data);
                
                // Ако има налични сцени, избираме първата автоматично
                if (scenesRes.data.length > 0) setSelectedScene(scenesRes.data[0]);
            } catch (e) {
                console.error('Неуспешно зареждане на началните данни:', e);
            } finally {
                setLoading(false);
            }
        };
        init();
    }, []);

    // ── Опресняване на сцените (Scene Refresh) ────────────────────────────────────────────────────────
    // useCallback се използва, за да не се пресъздава функцията при всяко рендиране
    const fetchScenes = useCallback(async (silent = false) => {
        // Ако silent е false, показваме индикатор за зареждане в бутона за refresh
        if (!silent) setRefreshing(true);
        try {
            // Добавяме _t параметър с текущото време, за да предотвратим кеширането от браузъра
            const res = await api.get<Scene[]>(`/scenes?_t=${Date.now()}`);
            setScenes(res.data);
            return res.data;
        } catch (e) {
            console.error('Неуспешно опресняване на сцените:', e);
            return [];
        } finally {
            setRefreshing(false);
        }
    }, []);

    // ── Polling (редовно проверяване) на статуса на активната задача ──────────────────────────────────────────────────────────
    useEffect(() => {
        // Ако няма активна задача или тя вече е завършила/пропаднала, не правим нищо
        if (!activeJob || activeJob.status === 'completed' || activeJob.status === 'failed') return;

        // Създаване на интервал за проверка на състоянието на всеки 3 секунди
        const interval = setInterval(async () => {
            try {
                // Извличане на всички текущи ETL задачи
                const res = await api.get('/scenes/etl-status');
                const jobs: any[] = res.data;
                // Намиране на задачата, която ни интересува
                const job = jobs.find(j => j.id === activeJob.job_id);
                if (!job) return;

                const progress = job.payload?.progress ?? activeJob.progress;
                const scene_id_str = job.payload?.scene_id_str ?? activeJob.scene_id_str;

                // Актуализиране на състоянието
                setActiveJob(prev => prev ? {
                    ...prev,
                    status: job.status,
                    progress,
                    scene_id_str,
                } : null);

                // Ако задачата е успешно завършена
                if (job.status === 'completed') {
                    clearInterval(interval); // Спиране на интервала
                    // Добавяме забавяне от 1.5 сек, за да сме сигурни, че промените в базата данни са отразени
                    setTimeout(async () => {
                        let allScenes = await fetchScenes(true);
                        // Ако сцената все още липсва, изчакваме още 2 секунди и опитваме пак
                        if (!allScenes || allScenes.length === 0) {
                            await new Promise(r => setTimeout(r, 2000));
                            allScenes = await fetchScenes(true);
                        }
                        
                        // Автоматично избиране на новосъздадената сцена (предполага се, че е първа)
                        if (allScenes && allScenes.length > 0) {
                            setSelectedScene(allScenes[0]);
                        }
                    }, 1500);
                }
                // При неуспех също спираме интервала
                if (job.status === 'failed') {
                    clearInterval(interval);
                }
            } catch {/* Игнорираме мълчаливо мрежови грешки при polling-а */}
        }, 3000);

        // Почистване на интервала при демонтиране или промяна в зависимостите
        return () => clearInterval(interval);
    }, [activeJob, fetchScenes]);

    // Автоматично фоново опресняване на сцените на всеки 30 секунди
    useEffect(() => {
        const iv = setInterval(() => fetchScenes(true), 30_000);
        return () => clearInterval(iv);
    }, [fetchScenes]);

    // ── Изпращане на заявка за нов анализ (AOI Submit) ───────────────────────────────────────────────────────────
    const handleAoiSubmit = useCallback(async (bbox: BBox, aoi_name: string, display_name?: string) => {
        try {
            // Изпращане на POST заявка към бекенда за стартиране на обработка на избраната зона
            const res = await api.post('/scenes/analyze-aoi', {
                bbox,
                aoi_name,
                display_name,
                cloud_max: 30, // Максимално позволено облачно покритие
            });
            // Запазване на ID-то на върнатата задача за последващо следене (polling)
            setActiveJob({
                job_id: res.data.job_id,
                aoi_name: display_name || aoi_name,
                bbox,
                status: 'pending',
                progress: 0,
            });
        } catch (e: any) {
            console.error('Неуспешно стартиране на AOI анализ:', e);
            alert(e?.response?.data?.detail ?? 'Неуспешно стартиране на анализа. Проверете вашите права.');
        }
    }, []);

    // ── Производни данни (Derived Data) ──────────────────────────────────────────────────────────────
    // Сортиране на сцените по дата на заснемане в низходящ ред (най-новите първи)
    const sortedScenes = [...scenes].sort(
        (a, b) => new Date(b.acquisition_date).getTime() - new Date(a.acquisition_date).getTime()
    );

    // Конструиране на URL адреса за GeoTIFF файла на избраната сцена
    const selectedSceneUrl = selectedScene
        ? `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/data/inference/${selectedScene.scene_id}_classification.tif`
        : undefined;

    // ── Рендиране на потребителския интерфейс (Render) ───────────────────────────────────────────────────────────────
    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="flex h-full flex-col overflow-hidden bg-muted/20">
            {/* Горен панел (Header) */}
            <div className="flex-none px-4 py-3 m-4 mb-0 rounded-lg flex items-center justify-between border-2 border-slate-300 dark:border-slate-700 bg-background shadow-sm z-10">
                <div className="flex items-center gap-6">
                    <h2 className="text-3xl font-bold tracking-tight">Monitoring Map</h2>
                    {/* Табове за превключване между Карта и Детайлен Анализ */}
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-[400px]">
                        <TabsList className="grid w-full grid-cols-2">
                            <TabsTrigger value="map">Explorer</TabsTrigger>
                            <TabsTrigger value="analysis" disabled={!selectedScene}>Analysis Dashboard</TabsTrigger>
                        </TabsList>
                    </Tabs>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Satellite className="h-3.5 w-3.5" />
                    Draw a zone on the map to start analysis
                </div>
            </div>

            {/* Изглед Карта (Map View) */}
            <div className={`flex-1 min-h-0 p-4 ${activeTab === 'map' ? 'block' : 'hidden'}`}>
                <div className="grid h-full grid-cols-1 gap-4 lg:grid-cols-4">
                    {/* ── Странична лента (Sidebar) ── */}
                    <div className="flex flex-col h-full space-y-4 lg:col-span-1 min-h-0">

                        {/* Карточка за статуса на активна фонова задача (Active job status card) */}
                        {activeJob && (
                            <Card className={`shrink-0 border-2 ${
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
                                        Zone Analysis (AOI)
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-2">
                                    <p className="text-[11px] font-mono truncate text-muted-foreground">{activeJob.aoi_name}</p>
                                    <p className="text-[10px] text-muted-foreground">
                                        [{activeJob.bbox.map(v => v.toFixed(3)).join(', ')}]
                                    </p>
                                    {/* Визуализация на прогрес бар, ако задачата се изпълнява */}
                                    {(activeJob.status === 'pending' || activeJob.status === 'processing') ? (
                                        <>
                                            <Progress
                                                value={activeJob.progress}
                                                className="h-1.5"
                                            />
                                            <div className="flex items-center justify-between">
                                                <Badge
                                                    variant="secondary"
                                                    className="text-[10px] uppercase"
                                                >
                                                    {activeJob.status === 'pending' ? (
                                                        <><Clock className="h-2.5 w-2.5 mr-1" />Queued</>
                                                    ) : activeJob.status}
                                                </Badge>
                                                <span className="text-[10px] text-muted-foreground">
                                                    {Math.round(activeJob.progress)}%
                                                </span>
                                            </div>
                                        </>
                                    ) : (
                                        // Съобщения при завършена задача (успех или грешка)
                                        <div className="flex items-center justify-between pt-1">
                                            {activeJob.status === 'completed' ? (
                                                <p className="text-[10px] text-green-600 font-medium">
                                                    ✓ Classification loaded
                                                </p>
                                            ) : (
                                                <p className="text-[10px] text-destructive">
                                                    Pipeline error — check the logs
                                                </p>
                                            )}
                                            {/* Бутон за премахване на известието за завършена задача */}
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                className="h-6 text-[10px] px-2 shrink-0"
                                                onClick={() => setActiveJob(null)}
                                            >
                                                Dismiss
                                            </Button>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        )}

                        {/* Списък с наличните сцени (Available scenes) */}
                        <Card className="flex-1 flex flex-col min-h-0">
                            <CardHeader className="pb-3 shrink-0">
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
                            <CardContent className="p-0 flex-1 overflow-y-auto min-h-0">
                                <div className="flex flex-col">
                                    {/* Ако няма сцени, показваме празно състояние с инструкции */}
                                    {sortedScenes.length === 0 ? (
                                        <div className="p-8 text-xs text-muted-foreground text-center flex flex-col items-center gap-2">
                                            <Layers className="h-8 w-8 opacity-20" />
                                            <p>No available scenes.</p>
                                            <p className="text-[10px]">Draw a zone on the map to start your first analysis.</p>
                                        </div>
                                    ) : (
                                        // Рендиране на списъка със сцени
                                        sortedScenes.map(scene => (
                                            <div
                                                key={scene.id}
                                                onClick={() => setSelectedScene(scene)}
                                                className={`p-3 border-b last:border-0 cursor-pointer hover:bg-muted/50 transition-colors ${
                                                    selectedScene?.id === scene.id
                                                        ? 'bg-primary/5 border-l-4 border-l-primary' // Стилизиране на активно избраната сцена
                                                        : ''
                                                }`}
                                            >
                                                <div className="flex flex-col gap-1 min-w-0">
                                                    <span className={`text-xs font-bold truncate block ${scene.display_name ? 'font-sans' : 'font-mono'}`}>
                                                        {scene.display_name || scene.scene_id}
                                                    </span>
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-[10px] text-muted-foreground">
                                                            {scene.acquisition_date}
                                                        </span>
                                                        <Badge variant="outline" className="text-[9px] h-4">
                                                            {scene.cloud_cover !== null && scene.cloud_cover !== undefined
                                                                ? `${scene.cloud_cover.toFixed(1)}% clouds`
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

                        {/* Инструкции за работа (Instructions card) */}
                        <Card className="border-dashed shrink-0">
                            <CardContent className="p-4 space-y-2">
                                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">How it works</p>
                                <ol className="text-[11px] text-muted-foreground space-y-1.5 list-decimal list-inside">
                                    <li>Click <strong>"Analyze Zone"</strong> on the map</li>
                                    <li>Drag to draw your area of interest</li>
                                    <li>Click <strong>"Analyze"</strong></li>
                                    <li>Wait for the pipeline to complete</li>
                                    <li>The classification layer will load automatically</li>
                                </ol>
                            </CardContent>
                        </Card>
                    </div>

                    {/* ── Главен контейнер за Картата (Map) ── */}
                    <div className="lg:col-span-3 h-full min-h-0">
                        <Card className="h-full">
                            <CardContent className="p-0 h-full">
                                <AppMap
                                    regions={regions}
                                    selectedSceneUrl={selectedSceneUrl}
                                    onAoiSubmit={canAnalyze ? handleAoiSubmit : undefined}
                                />
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>

            {/* Изглед Анализ на Сцена (Scene Analysis Section) */}
            {/* Показва се само ако е избран таб 'analysis' и има избрана сцена */}
            {activeTab === 'analysis' && selectedScene && (
                <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-6">
                    <div className="flex items-center justify-between">
                        <h3 className="text-2xl font-bold tracking-tight">Scene Analysis: {selectedScene.display_name || selectedScene.scene_id}</h3>
                        <Badge variant="outline" className="text-xs">
                            {selectedScene.acquisition_date}
                        </Badge>
                    </div>
                    {/* Компонент със статистически данни */}
                    <SceneAnalysis scene={selectedScene} />
                    <div className="grid gap-4">
                        {/* Компонент с графики за SHAP обяснимост */}
                        <ShapExplanation sceneId={selectedScene.id} />
                    </div>
                </div>
            )}
        </div>
    );
}
