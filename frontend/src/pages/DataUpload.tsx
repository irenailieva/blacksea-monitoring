import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Upload, FileType, CheckCircle2, AlertCircle, Activity } from 'lucide-react';
import api from '@/api/axios';
import { EtlMonitor } from '@/components/EtlMonitor';

export default function DataUpload() {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [status, setStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setStatus(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setStatus(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            // Placeholder endpoint - in a real app this would match the FastAPI backend
            await api.post('/scenes/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setStatus({ type: 'success', message: 'File uploaded successfully!' });
            setFile(null);
        } catch (error) {
            console.error('Upload failed:', error);
            setStatus({ type: 'error', message: 'Upload failed. Please try again.' });
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="container mx-auto py-6 space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">Data Upload</h2>
                <Button 
                    variant="secondary"
                    onClick={async () => {
                        try {
                            await api.post('/scenes/etl-trigger');
                            setStatus({ type: 'success', message: 'Automated ETL triggered successfully!'});
                        } catch(e) {
                            setStatus({ type: 'error', message: 'Failed to trigger ETL.'});
                        }
                    }}
                >
                    <Activity className="mr-2 h-4 w-4 text-primary" /> 
                    Trigger Sentinel-2 Fetch
                </Button>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Manual Upload</CardTitle>
                        <CardDescription>
                            Upload Sentinel-2 GeoTIFFs, Drone Orthomosaics, or GPS data (CSV/GeoJSON).
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid w-full items-center gap-1.5 focus-within:ring-2 focus-within:ring-primary/20 rounded-lg p-1 transition-all">
                            <Label htmlFor="data-file" className="px-1 text-xs font-semibold uppercase text-muted-foreground tracking-wider">Select Source File</Label>
                            <label
                                htmlFor="data-file"
                                className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer bg-muted/30 hover:bg-muted/50 border-muted-foreground/25 hover:border-primary/50 transition-all"
                            >
                                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                    <Upload className="w-8 h-8 mb-3 text-muted-foreground/60" />
                                    <p className="mb-2 text-sm text-muted-foreground text-center px-4">
                                        <span className="font-semibold">Click to upload</span> or drag and drop
                                    </p>
                                    <p className="text-xs text-muted-foreground/60">
                                        GeoTIFF, Drone Tiles, or GPS CSV (MAX. 500MB)
                                    </p>
                                </div>
                                <Input
                                    id="data-file"
                                    type="file"
                                    className="hidden"
                                    accept=".tif,.tiff,.csv,.geojson,.json"
                                    onChange={handleFileChange}
                                    disabled={uploading}
                                />
                            </label>
                        </div>

                        {file && (
                            <div className="flex items-center gap-3 p-3 bg-primary/5 rounded-lg border border-primary/20 animate-in fade-in slide-in-from-top-1">
                                <div className="bg-primary/10 p-2 rounded-md">
                                    <FileType className="h-5 w-5 text-primary" />
                                </div>
                                <div className="flex flex-col overflow-hidden">
                                    <span className="text-sm font-medium truncate">{file.name}</span>
                                    <span className="text-xs text-muted-foreground">
                                        {(file.size / (1024 * 1024)).toFixed(2)} MB
                                    </span>
                                </div>
                            </div>
                        )}

                        {status && (
                            <div className={`p-3 rounded-md flex items-center gap-2 text-sm ${status.type === 'success' ? 'bg-green-500/10 text-green-500' : 'bg-destructive/10 text-destructive'
                                }`}>
                                {status.type === 'success' ? (
                                    <CheckCircle2 className="h-4 w-4" />
                                ) : (
                                    <AlertCircle className="h-4 w-4" />
                                )}
                                {status.message}
                            </div>
                        )}

                        <Button
                            className="w-full"
                            disabled={!file || uploading}
                            onClick={handleUpload}
                        >
                            {uploading ? (
                                <>Processing...</>
                            ) : (
                                <>
                                    <Upload className="mr-2 h-4 w-4" />
                                    Upload & Process
                                </>
                            )}
                        </Button>
                    </CardContent>
                </Card>

                <div className="grid gap-6 md:grid-cols-2">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Activity className="h-5 w-5" />
                                Processing Monitor
                            </CardTitle>
                            <CardDescription>
                                Real-time status of Sentinel-2 scene classification jobs.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <EtlMonitor />
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Guidelines</CardTitle>
                            <CardDescription>
                                Important information for successful data processing.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4 text-sm">
                            <div className="space-y-2">
                                <h4 className="font-medium">GeoTIFFs</h4>
                                <ul className="list-disc pl-4 space-y-1 text-muted-foreground">
                                    <li>Must be in EPSG:4326 or UTM 35N projection.</li>
                                    <li>Max file size: 500MB.</li>
                                    <li>Ensure bands are correctly ordered (B4, B3, B2, B8 for Sentinel-2).</li>
                                </ul>
                            </div>
                            <div className="space-y-2">
                                <h4 className="font-medium">GPS Data</h4>
                                <ul className="list-disc pl-4 space-y-1 text-muted-foreground">
                                    <li>CSV files must have 'lat' and 'lon' columns.</li>
                                    <li>GeoJSON must contain FeatureCollection of Polygons or Points.</li>
                                </ul>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
