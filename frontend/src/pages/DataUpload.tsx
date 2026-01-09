import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Upload, FileType, CheckCircle2, AlertCircle } from 'lucide-react';
import api from '@/api/axios';

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
            await api.post('/data/upload', formData, {
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
                        <div className="grid w-full items-center gap-1.5">
                            <Label htmlFor="data-file">Select File</Label>
                            <Input 
                                id="data-file" 
                                type="file" 
                                accept=".tif,.tiff,.csv,.geojson,.json" 
                                onChange={handleFileChange}
                                disabled={uploading}
                            />
                            <p className="text-xs text-muted-foreground">
                                Supported formats: GeoTIFF (.tif), CSV, GeoJSON
                            </p>
                        </div>

                        {file && (
                            <div className="flex items-center gap-2 p-2 bg-muted rounded-md border">
                                <FileType className="h-4 w-4 text-primary" />
                                <span className="text-sm truncate flex-1">{file.name}</span>
                                <span className="text-xs text-muted-foreground">
                                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                                </span>
                            </div>
                        )}

                        {status && (
                            <div className={`p-3 rounded-md flex items-center gap-2 text-sm ${
                                status.type === 'success' ? 'bg-green-500/10 text-green-500' : 'bg-destructive/10 text-destructive'
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
    );
}
