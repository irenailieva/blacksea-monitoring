import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Loader2, CheckCircle2, AlertCircle, Clock } from 'lucide-react';
import api from '@/api/axios';

interface JobStatus {
    id: number;
    job_type: string;
    status: 'pending' | 'running' | 'processing' | 'completed' | 'failed';
    payload?: any;
    started_at?: string;
    finished_at?: string;
}

export function EtlMonitor() {
    const [jobs, setJobs] = useState<JobStatus[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchStatus = async () => {
        try {
            // In a real scenario, this would be a WebSocket or polling endpoint
            const response = await api.get('/scenes/etl-status');
            setJobs(response.data);
        } catch (error) {
            console.error('Failed to fetch ETL status:', error);
            // Fallback to some mock data if endpoint is not yet ready
            /* 
            setJobs([
               { id: 1, sentinel_id: 'S2A_MSIL2A_20230715', status: 'processing', progress: 45, started_at: '2023-11-20T10:00:00Z' },
               { id: 2, sentinel_id: 'S2B_MSIL2A_20230720', status: 'pending', progress: 0, started_at: '2023-11-20T10:05:00Z' }
           ]);
           */
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    if (loading && jobs.length === 0) {
        return (
            <div className="flex items-center justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (jobs.length === 0) {
        return (
            <div className="p-4 text-center text-sm text-muted-foreground">
                No active processing jobs.
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {jobs.map((job) => (
                <div key={job.id} className="space-y-2 border-b last:border-0 pb-4 last:pb-0">
                    <div className="flex items-center justify-between">
                        <div className="flex flex-col">
                            <span className="text-xs font-mono font-bold">
                                {job.payload?.sentinel_id || job.job_type}
                            </span>
                            <span className="text-[10px] text-muted-foreground">Started: {job.started_at ? new Date(job.started_at).toLocaleString() : 'N/A'}</span>
                        </div>
                        <Badge variant={
                            job.status === 'completed' ? 'default' :
                                job.status === 'failed' ? 'destructive' :
                                    (job.status === 'running' || job.status === 'processing') ? 'secondary' : 'outline'
                        } className="text-[10px] uppercase">
                            {job.status}
                        </Badge>
                    </div>
                    {(job.status === 'running' || job.status === 'processing') && (
                        <div className="space-y-1">
                            <Progress value={job.payload?.progress || 0} className="h-1" />
                            <div className="flex justify-end">
                                <span className="text-[10px] text-muted-foreground">{job.payload?.progress || 0}%</span>
                            </div>
                        </div>
                    )}
                    <div className="flex items-center gap-2">
                        {job.status === 'completed' && <CheckCircle2 className="h-3 w-3 text-green-500" />}
                        {job.status === 'failed' && <AlertCircle className="h-3 w-3 text-destructive" />}
                        {(job.status === 'running' || job.status === 'processing') && <Loader2 className="h-3 w-3 animate-spin text-primary" />}
                        {job.status === 'pending' && <Clock className="h-3 w-3 text-muted-foreground" />}
                        <span className="text-[10px] capitalize text-muted-foreground">{job.status}</span>
                    </div>
                </div>
            ))}
        </div>
    );
}
