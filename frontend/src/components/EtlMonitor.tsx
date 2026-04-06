import { useEffect, useState, useCallback } from 'react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Loader2, CheckCircle2, AlertCircle, Clock, RefreshCw, RotateCcw } from 'lucide-react';
import api from '@/api/axios';

interface JobStatus {
    id: number;
    job_type: string;
    status: 'pending' | 'running' | 'processing' | 'completed' | 'failed';
    payload?: { progress?: number; sentinel_id?: string; scene_id_str?: string; scene_id?: number; file_path?: string; [key: string]: any };
    started_at?: string;
    finished_at?: string;
}

const STATUS_ORDER: Record<string, number> = { processing: 0, running: 0, pending: 1, failed: 2, completed: 3 };

function isActive(status: string) {
    return status === 'pending' || status === 'running' || status === 'processing';
}

export function EtlMonitor() {
    const [jobs, setJobs] = useState<JobStatus[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [retrying, setRetrying] = useState<Record<number, boolean>>({});

    const fetchStatus = useCallback(async (manual = false) => {
        if (manual) setRefreshing(true);
        try {
            const response = await api.get('/scenes/etl-status');
            const sorted = (response.data as JobStatus[]).sort((a, b) => {
                const orderDiff = (STATUS_ORDER[a.status] ?? 4) - (STATUS_ORDER[b.status] ?? 4);
                return orderDiff !== 0 ? orderDiff : b.id - a.id;
            });
            setJobs(sorted);
        } catch (error) {
            console.error('Failed to fetch ETL status:', error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, []);

    const retryJob = useCallback(async (jobId: number) => {
        setRetrying(prev => ({ ...prev, [jobId]: true }));
        try {
            await api.post(`/scenes/etl-retry/${jobId}`);
            await fetchStatus();
        } catch (err: any) {
            const detail = err?.response?.data?.detail ?? 'Retry failed';
            alert(detail);
        } finally {
            setRetrying(prev => ({ ...prev, [jobId]: false }));
        }
    }, [fetchStatus]);

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(() => fetchStatus(), 5000);
        return () => clearInterval(interval);
    }, [fetchStatus]);

    const hasActiveJobs = jobs.some(j => isActive(j.status));

    return (
        <div className="space-y-3">
            {/* Header row */}
            <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                    {hasActiveJobs
                        ? `${jobs.filter(j => isActive(j.status)).length} job(s) in progress…`
                        : 'No active jobs'}
                </span>
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    onClick={() => fetchStatus(true)}
                    disabled={refreshing}
                    title="Refresh"
                >
                    <RefreshCw className={`h-3 w-3 ${refreshing ? 'animate-spin' : ''}`} />
                </Button>
            </div>

            {loading && jobs.length === 0 ? (
                <div className="flex items-center justify-center p-6">
                    <Loader2 className="h-7 w-7 animate-spin text-primary" />
                </div>
            ) : jobs.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                    No ETL jobs found.
                </div>
            ) : (
                jobs.map((job) => {
                    const progress = job.payload?.progress ?? 0;
                    const label = job.payload?.scene_id_str ?? job.payload?.sentinel_id ?? job.job_type.replace(/_/g, ' ');
                    const active = isActive(job.status);

                    return (
                        <div
                            key={job.id}
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
                                    <span className="text-xs font-mono font-semibold truncate capitalize">
                                        {label}
                                    </span>
                                    <span className="text-[10px] text-muted-foreground">
                                        #{job.id} · Started:{' '}
                                        {job.started_at
                                            ? new Date(job.started_at).toLocaleTimeString()
                                            : 'N/A'}
                                        {job.finished_at && (
                                            <>
                                                {' '}→ Finished:{' '}
                                                {new Date(job.finished_at).toLocaleTimeString()}
                                            </>
                                        )}
                                    </span>
                                </div>
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

                            {/* Progress bar for active or pending jobs */}
                            {(active || job.status === 'completed') && (
                                <div className="space-y-1">
                                    <Progress
                                        value={job.status === 'completed' ? 100 : progress}
                                        className="h-1.5"
                                    />
                                    <div className="flex justify-between items-center">
                                        <div className="flex items-center gap-1">
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
                                                    ? 'Queued — waiting to start'
                                                    : job.status}
                                            </span>
                                        </div>
                                        <span className="text-[10px] text-muted-foreground">
                                            {job.status === 'completed' ? 100 : progress}%
                                        </span>
                                    </div>
                                </div>
                            )}

                            {/* Failed: show error + retry button */}
                            {job.status === 'failed' && (
                                <div className="flex items-center justify-between gap-2 pt-0.5">
                                    <div className="flex items-center gap-1 min-w-0">
                                        <AlertCircle className="h-3 w-3 text-destructive shrink-0" />
                                        <span className="text-[10px] text-destructive truncate">
                                            {job.job_type === 'manual_upload' && job.payload?.file_path
                                                ? `File: ${job.payload.file_path.split('/').pop()}`
                                                : 'Pipeline failed — check logs'}
                                        </span>
                                    </div>
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        className="h-5 px-2 text-[10px] shrink-0 border-destructive/40 hover:bg-destructive/10"
                                        disabled={retrying[job.id]}
                                        onClick={() => retryJob(job.id)}
                                        title="Retry this job"
                                    >
                                        {retrying[job.id]
                                            ? <Loader2 className="h-2.5 w-2.5 animate-spin" />
                                            : <><RotateCcw className="h-2.5 w-2.5 mr-1" />Retry</>
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
