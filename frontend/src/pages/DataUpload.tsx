import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Upload, FileType, CheckCircle2, AlertCircle, Activity } from 'lucide-react';
import api from '@/api/axios';
import { EtlMonitor } from '@/components/EtlMonitor';

export default function DataUpload() {
    const [files, setFiles] = useState<File[]>([]);
    const [uploading, setUploading] = useState(false);
    const [status, setStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setFiles(Array.from(e.target.files));
            setStatus(null);
        }
    };

    const handleUpload = async () => {
        if (files.length === 0) return;

        setUploading(true);
        setStatus(null);

        try {
            await Promise.all(files.map(async (file) => {
                const formData = new FormData();
                formData.append('file', file);
                
                return api.post('/scenes/upload', formData, {
                    headers: {
                        'Content-Type': undefined
                    }
                });
            }));
            
            setStatus({ type: 'success', message: 'All files uploaded successfully!' });
            setFiles([]);
        } catch (error: any) {
            console.error('Upload failed:', error);
            
            let errorMsg = 'One or more uploads failed. Please try again.';
            if (error.response?.data?.detail) {
                errorMsg = `Upload failed: ${error.response.data.detail}`;
            } else if (error.message) {
                errorMsg = `Upload error: ${error.message}`;
            }
            setStatus({ type: 'error', message: errorMsg });
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="container mx-auto py-8 space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-primary">Data Upload</h2>
                    <p className="text-muted-foreground mt-1 text-sm">Upload local data or trigger automated Sentinel-2 processing.</p>
                </div>
                <Button 
                    size="lg"
                    className="shadow-md hover:shadow-lg transition-shadow"
                    onClick={async () => {
                        try {
                            await api.post('/scenes/etl-trigger');
                            setStatus({ type: 'success', message: 'Automated ETL triggered successfully!'});
                        } catch(e) {
                            setStatus({ type: 'error', message: 'Failed to trigger ETL.'});
                        }
                    }}
                >
                    <Activity className="mr-2 h-4 w-4" /> 
                    Trigger Sentinel-2 Fetch
                </Button>
            </div>

            {/* GUIDELINES PANEL - TOP, HORIZONTAL */}
            <Card className="w-full bg-primary/5 border-primary/10 shadow-sm">
                <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <AlertCircle className="w-5 h-5 text-primary" />
                        Processing Guidelines
                    </CardTitle>
                    <CardDescription>
                        Important information to guarantee successful data ingestion and modeling.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-6 md:grid-cols-2 text-sm">
                        <div className="space-y-3 bg-background/50 p-4 rounded-lg border border-border/50">
                            <h4 className="font-semibold text-primary">GeoTIFF Uploads</h4>
                            <ul className="list-disc pl-4 space-y-1.5 text-muted-foreground">
                                <li>Must be in <span className="font-medium text-foreground">EPSG:4326</span> or <span className="font-medium text-foreground">UTM 35N</span> projection.</li>
                                <li>Maximum file size limit: <span className="font-medium text-foreground">500MB</span>.</li>
                                <li>Ensure raster bands are correctly ordered (e.g. <span className="font-medium text-foreground">B4, B3, B2, B8</span> for Sentinel-2).</li>
                            </ul>
                        </div>
                        <div className="space-y-3 bg-background/50 p-4 rounded-lg border border-border/50">
                            <h4 className="font-semibold text-primary">GPS & Vector Data</h4>
                            <ul className="list-disc pl-4 space-y-1.5 text-muted-foreground">
                                <li>CSV files must explicitly contain <span className="font-medium text-foreground">'lat'</span> and <span className="font-medium text-foreground">'lon'</span> columns.</li>
                                <li>GeoJSON files must contain a <span className="font-medium text-foreground">FeatureCollection</span> of Polygons or Points.</li>
                                <li>Geometry must overlap with configured system regions (AOI).</li>
                            </ul>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* BOTTOM PANELS */}
            <div className="grid gap-8 lg:grid-cols-5">
                
                {/* MANUAL UPLOAD - LEFT WIDER COLUMN */}
                <Card className="lg:col-span-3 shadow-md border-border/50">
                    <CardHeader className="bg-muted/20 border-b border-border/50 pb-4">
                        <CardTitle className="flex items-center gap-2">
                            <Upload className="w-5 h-5" />
                            Manual Upload
                        </CardTitle>
                        <CardDescription>
                            Manually ingest Sentinel-2 GeoTIFFs, Drone orthomosaics, or GPS tracking logs.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6 pt-6">
                        <div className="grid w-full items-center gap-1.5 focus-within:ring-2 focus-within:ring-primary/20 rounded-xl p-1 transition-all">
                            <Label htmlFor="data-file" className="px-1 text-xs font-semibold uppercase text-muted-foreground tracking-wider">Select Source Files</Label>
                            <label
                                htmlFor="data-file"
                                className="flex flex-col items-center justify-center w-full h-40 border-2 border-dashed rounded-xl cursor-pointer bg-muted/20 hover:bg-muted/40 border-primary/20 hover:border-primary/50 transition-all duration-300"
                            >
                                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                    <div className="bg-primary/10 p-3 rounded-full mb-4">
                                        <Upload className="w-8 h-8 text-primary" />
                                    </div>
                                    <p className="mb-2 text-sm text-foreground text-center px-4">
                                        <span className="font-semibold text-primary hover:underline">Click to browse</span> or drag and drop files here
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                        Support for .TIF, .TIFF, .CSV, .GEOJSON
                                    </p>
                                </div>
                                <Input
                                    id="data-file"
                                    type="file"
                                    className="hidden"
                                    multiple
                                    accept=".tif,.tiff,.csv,.geojson,.json"
                                    onChange={handleFileChange}
                                    disabled={uploading}
                                />
                            </label>
                        </div>

                        {files.length > 0 && (
                            <div className="space-y-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                                {files.map((file, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-3 bg-background rounded-lg border shadow-sm animate-in fade-in slide-in-from-bottom-2">
                                        <div className="flex items-center gap-3">
                                            <div className="bg-primary/10 p-2 rounded-md">
                                                <FileType className="h-5 w-5 text-primary" />
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-sm font-medium">{file.name}</span>
                                                <span className="text-xs text-muted-foreground">
                                                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                                                </span>
                                            </div>
                                        </div>
                                        <CheckCircle2 className="h-4 w-4 text-green-500 opacity-60" />
                                    </div>
                                ))}
                            </div>
                        )}

                        {status && (
                            <div className={`p-4 rounded-lg flex items-center gap-3 text-sm font-medium animate-in fade-in zoom-in-95 ${
                                status.type === 'success' ? 'bg-green-500/10 text-green-600 border border-green-500/20' : 'bg-destructive/10 text-destructive border border-destructive/20'
                            }`}>
                                {status.type === 'success' ? (
                                    <CheckCircle2 className="h-5 w-5" />
                                ) : (
                                    <AlertCircle className="h-5 w-5" />
                                )}
                                {status.message}
                            </div>
                        )}

                        <Button
                            size="lg"
                            className="w-full font-semibold"
                            disabled={files.length === 0 || uploading}
                            onClick={handleUpload}
                        >
                            {uploading ? (
                                <span className="flex items-center gap-2">
                                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent" />
                                    Processing Uploads...
                                </span>
                            ) : (
                                <>
                                    <Upload className="mr-2 h-4 w-4" />
                                    Start Secure Upload
                                </>
                            )}
                        </Button>
                    </CardContent>
                </Card>

                {/* PROCESSING MONITOR - RIGHT COLUMN */}
                <Card className="lg:col-span-2 shadow-md border-border/50 bg-gradient-to-br from-background to-muted/20">
                    <CardHeader className="bg-muted/20 border-b border-border/50 pb-4">
                        <div className="flex items-center justify-between">
                            <CardTitle className="flex items-center gap-2">
                                <Activity className="h-5 w-5 text-primary" />
                                System Monitor
                            </CardTitle>
                            <span className="relative flex h-3 w-3">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                            </span>
                        </div>
                        <CardDescription>
                            Real-time tracking of active and recent pipelines.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="p-0">
                        {/* Assuming EtlMonitor component wraps its own padding/scrolling properly, but adding a wrapper to contain it */}
                        <div className="p-4 h-[400px] overflow-y-auto custom-scrollbar">
                            <EtlMonitor />
                        </div>
                    </CardContent>
                </Card>

            </div>
        </div>
    );
}
