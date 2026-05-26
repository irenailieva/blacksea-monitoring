import { useEffect, useState, useCallback } from 'react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Loader2, CheckCircle2, AlertCircle, Clock, RefreshCw, RotateCcw } from 'lucide-react';
import api from '@/api/axios';

// Интерфейс, описващ състоянието на дадена ETL (Extract, Transform, Load) задача
interface JobStatus {
    id: number; // Уникален идентификатор на задачата
    job_type: string; // Тип на задачата (напр. 'sentinel_download', 'manual_upload')
    status: 'pending' | 'running' | 'processing' | 'completed' | 'failed'; // Текущо състояние
    // Допълнителни данни за задачата (полезен товар), включително прогрес
    payload?: { progress?: number; sentinel_id?: string; scene_id_str?: string; scene_id?: number; file_path?: string; [key: string]: any };
    started_at?: string; // Време на стартиране
    finished_at?: string; // Време на приключване
}

// Речник за определяне на приоритета при сортиране на задачите (активните са най-отгоре)
const STATUS_ORDER: Record<string, number> = { processing: 0, running: 0, pending: 1, failed: 2, completed: 3 };

/**
 * Бекендът съхранява датите в UTC формат, но понякога пропуска 'Z' накрая.
 * Тази функция добавя 'Z', ако липсва, за да може браузърът правилно да ги конвертира в локално време.
 */
function parseUTCDate(ts: string): Date {
    return new Date(ts.endsWith('Z') ? ts : ts + 'Z');
}

// Помощна функция, която проверява дали задачата в момента е активна (не е приключила или провалена)
function isActive(status: string) {
    return status === 'pending' || status === 'running' || status === 'processing';
}

// Компонент за мониторинг на активните ETL процеси
export function EtlMonitor() {
    // Състояния на компонента
    const [jobs, setJobs] = useState<JobStatus[]>([]); // Списък със задачи
    const [loading, setLoading] = useState(true); // Флаг за първоначално зареждане
    const [refreshing, setRefreshing] = useState(false); // Флаг за ръчно опресняване
    const [retrying, setRetrying] = useState<Record<number, boolean>>({}); // Проследяване кои задачи се рестартират в момента

    // Функция за извличане на статуса на задачите от сървъра
    const fetchStatus = useCallback(async (manual = false) => {
        if (manual) setRefreshing(true);
        try {
            // Изпращане на GET заявка
            const response = await api.get('/scenes/etl-status');
            // Сортиране на задачите първо по статус (чрез STATUS_ORDER) и след това по ID (най-новите първи)
            const sorted = (response.data as JobStatus[]).sort((a, b) => {
                const orderDiff = (STATUS_ORDER[a.status] ?? 4) - (STATUS_ORDER[b.status] ?? 4);
                return orderDiff !== 0 ? orderDiff : b.id - a.id;
            });
            setJobs(sorted);
        } catch (error) {
            console.error('Неуспешно извличане на ETL статуса:', error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, []);

    // Функция за повторно стартиране (retry) на провалена задача
    const retryJob = useCallback(async (jobId: number) => {
        // Отбелязваме, че тази задача се рестартира (за показване на спинър)
        setRetrying(prev => ({ ...prev, [jobId]: true }));
        try {
            await api.post(`/scenes/etl-retry/${jobId}`);
            // След успешно рестартиране, обновяваме списъка със задачи
            await fetchStatus();
        } catch (err: any) {
            const detail = err?.response?.data?.detail ?? 'Неуспешно повторно стартиране';
            alert(detail);
        } finally {
            setRetrying(prev => ({ ...prev, [jobId]: false }));
        }
    }, [fetchStatus]);

    // Ефект за автоматично обновяване на данните на всеки 5 секунди
    useEffect(() => {
        fetchStatus(); // Първоначално извикване
        const interval = setInterval(() => fetchStatus(), 5000);
        // Почистване на интервала при демонтиране на компонента, за да се избегнат memory leaks
        return () => clearInterval(interval);
    }, [fetchStatus]);

    // Проверка дали има поне една активна задача в момента
    const hasActiveJobs = jobs.some(j => isActive(j.status));

    return (
        <div className="space-y-3">
            {/* Горен ред - Информация за задачите и бутон за ръчно обновяване */}
            <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                    {hasActiveJobs
                        ? `${jobs.filter(j => isActive(j.status)).length} задача(и) в прогрес…`
                        : 'Няма активни задачи'}
                </span>
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => fetchStatus(true)}
                    disabled={refreshing}
                    title="Опресни"
                >
                    {/* Анимация на въртене (spin), докато се опреснява */}
                    <RefreshCw className={`h-3 w-3 ${refreshing ? 'animate-spin' : ''}`} />
                </Button>
            </div>

            {/* Визуализация на състоянията: зареждане, празен списък или списък със задачи */}
            {loading && jobs.length === 0 ? (
                <div className="flex items-center justify-center p-6">
                    <Loader2 className="h-7 w-7 animate-spin text-primary" />
                </div>
            ) : jobs.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                    Не са намерени ETL процеси.
                </div>
            ) : (
                jobs.map((job) => {
                    const progress = job.payload?.progress ?? 0;
                    // Опит за намиране на най-подходящото име/идентификатор за визуализация
                    const label = job.payload?.display_name ?? job.payload?.scene_id_str ?? job.payload?.sentinel_id ?? job.job_type.replace(/_/g, ' ');
                    const active = isActive(job.status);

                    return (
                        <div
                            key={job.id}
                            // Динамично прилагане на CSS класове спрямо статуса на задачата
                            className={`space-y-2 rounded-md border px-3 py-2 ${
                                job.status === 'failed'
                                    ? 'border-destructive/30 bg-destructive/5'
                                    : job.status === 'completed'
                                    ? 'border-green-500/30 bg-green-500/5'
                                    : active
                                    ? 'border-primary/30 bg-primary/5'
                                    : ''
                            }`}
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex flex-col gap-0.5 min-w-0">
                                    {/* Визуализация на името на задачата */}
                                    <span className="text-xs font-mono font-semibold truncate block capitalize">
                                        {label}
                                    </span>
                                    {/* Визуализация на времето за стартиране и приключване */}
                                    <span className="text-[10px] text-muted-foreground">
                                        #{job.id} · Стартирана:{' '}
                                        {job.started_at
                                            ? parseUTCDate(job.started_at).toLocaleTimeString()
                                            : 'Н/Д'}
                                        {job.finished_at && (
                                            <>
                                                {' '}→ Завършена:{' '}
                                                {parseUTCDate(job.finished_at).toLocaleTimeString()}
                                            </>
                                        )}
                                    </span>
                                </div>
                                {/* Значка (Badge) с текущия статус */}
                                <Badge
                                    variant={
                                        job.status === 'completed'
                                            ? 'default'
                                            : job.status === 'failed'
                                            ? 'destructive'
                                            : active
                                            ? 'secondary'
                                            : 'outline'
                                    }
                                    className="text-[10px] uppercase ml-2 shrink-0"
                                >
                                    {job.status}
                                </Badge>
                            </div>

                            {/* Прогрес бар за активни или завършени задачи */}
                            {(active || job.status === 'completed') && (
                                <div className="space-y-1">
                                    <Progress
                                        value={job.status === 'completed' ? 100 : progress}
                                        className="h-1.5"
                                    />
                                    <div className="flex justify-between items-center">
                                        <div className="flex items-center gap-1">
                                            {/* Показване на съответната икона според статуса */}
                                            {job.status === 'completed' && (
                                                <CheckCircle2 className="h-3 w-3 text-green-500" />
                                            )}
                                            {job.status === 'failed' && (
                                                <AlertCircle className="h-3 w-3 text-destructive" />
                                            )}
                                            {(job.status === 'running' ||
                                                job.status === 'processing') && (
                                                <Loader2 className="h-3 w-3 animate-spin text-primary" />
                                            )}
                                            {job.status === 'pending' && (
                                                <Clock className="h-3 w-3 text-yellow-500 animate-pulse" />
                                            )}
                                            <span className="text-[10px] capitalize text-muted-foreground">
                                                {job.status === 'pending'
                                                    ? 'На опашката — изчаква старт'
                                                    : job.status}
                                            </span>
                                        </div>
                                        <span className="text-[10px] text-muted-foreground">
                                            {job.status === 'completed' ? 100 : progress}%
                                        </span>
                                    </div>
                                </div>
                            )}

                            {/* За провалени задачи: показва се съобщение за грешка и бутон за повторен опит */}
                            {job.status === 'failed' && (
                                <div className="flex items-center justify-between gap-2 pt-0.5">
                                    <div className="flex items-center gap-1 min-w-0">
                                        <AlertCircle className="h-3 w-3 text-destructive shrink-0" />
                                        <span className="text-[10px] text-destructive truncate">
                                            {job.job_type === 'manual_upload' && job.payload?.file_path
                                                ? `Файл: ${job.payload.file_path.split('/').pop()}`
                                                : 'Грешка в процеса — проверете логовете'}
                                        </span>
                                    </div>
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        className="h-5 px-2 text-[10px] shrink-0 border-destructive/40 hover:bg-destructive/10"
                                        disabled={retrying[job.id]}
                                        onClick={() => retryJob(job.id)}
                                        title="Повтори задачата"
                                    >
                                        {retrying[job.id]
                                            ? <Loader2 className="h-2.5 w-2.5 animate-spin" />
                                            : <><RotateCcw className="h-2.5 w-2.5 mr-1" />Опитай пак</>
                                        }
                                    </Button>
                                </div>
                            )}

                        </div>
                    );
                })
            )}
        </div>
    );
}
