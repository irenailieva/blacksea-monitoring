import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Upload, FileType, CheckCircle2, AlertCircle, Activity } from 'lucide-react';
import api from '@/api/axios';
import { EtlMonitor } from '@/components/EtlMonitor';

// Компонент за страница "Качване на данни" (Data Upload)
export default function DataUpload() {
    // Състояния
    const [files, setFiles] = useState<File[]>([]); // Списък с файлове, избрани от потребителя за качване
    const [uploading, setUploading] = useState(false); // Индикатор дали в момента се качват файлове
    // Състояние за обратна връзка към потребителя (успех или грешка)
    const [status, setStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);

    // Функция, която се извиква при избиране на файлове от input полето
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            // Преобразуване на FileList обекта в масив (Array) и запазване в състоянието
            setFiles(Array.from(e.target.files));
            setStatus(null); // Изчистване на предишни съобщения за статус
        }
    };

    // Асинхронна функция за обработка на качването към сървъра
    const handleUpload = async () => {
        if (files.length === 0) return; // Защита срещу качване на празен масив

        setUploading(true);
        setStatus(null);

        try {
            // Използване на Promise.all за паралелно качване на всички избрани файлове
            await Promise.all(files.map(async (file) => {
                // Използване на FormData, тъй като изпращаме binary данни (multipart/form-data)
                const formData = new FormData();
                formData.append('file', file);
                
                return api.post('/scenes/upload', formData, {
                    headers: {
                        // Axios автоматично ще зададе правилния Content-Type (вкл. boundary), 
                        // когато му се подаде undefined за Content-Type заедно с FormData
                        'Content-Type': undefined 
                    }
                });
            }));
            
            // При успешно качване на всички файлове
            setStatus({ type: 'success', message: 'All files uploaded successfully!' });
            setFiles([]); // Изчистване на списъка
        } catch (error: any) {
            console.error('Грешка при качване:', error);
            
            // Обработка на съобщението за грешка, идващо от бекенда (FastAPI detail) или от мрежата
            let errorMsg = 'An error occurred during upload. Please try again.';
            if (error.response?.data?.detail) {
                errorMsg = `Upload error: ${error.response.data.detail}`;
            } else if (error.message) {
                errorMsg = `Network error: ${error.message}`;
            }
            setStatus({ type: 'error', message: errorMsg });
        } finally {
            setUploading(false); // Край на процеса по качване
        }
    };

    return (
        <div className="h-full flex flex-col overflow-hidden">
            {/* Горен панел със заглавие и бутон за тригериране на ETL процес */}
            <div className="flex-none flex items-center justify-between px-4 pb-3">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight text-primary">Data Upload</h2>
                    <p className="text-muted-foreground mt-0.5 text-sm">Upload local data or trigger an automated Sentinel-2 pipeline.</p>
                </div>
                {/* Бутон за извикване на автоматизирания ETL (Extract, Transform, Load) процес */}
                <Button 
                    size="lg"
                    className="shadow-md hover:shadow-lg transition-shadow"
                    onClick={async () => {
                        try {
                            // Изпращане на заявка за стартиране на фонова задача на сървъра
                            await api.post('/scenes/etl-trigger');
                            setStatus({ type: 'success', message: 'Automated ETL pipeline started successfully!'});
                        } catch(e) {
                            setStatus({ type: 'error', message: 'Failed to start ETL pipeline.'});
                        }
                    }}
                >
                    <Activity className="mr-2 h-4 w-4" /> 
                    Fetch from Sentinel-2
                </Button>
            </div>

            {/* ИНФОРМАЦИОНЕН ПАНЕЛ (Указания) - ТОП, ХОРИЗОНТАЛЕН */}
            <Card className="flex-none mx-4 bg-primary/5 border-primary/10 shadow-sm">
                <CardHeader className="pb-2 pt-3">
                    <CardTitle className="text-base flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 text-primary" />
                        Processing Guidelines
                    </CardTitle>
                    <CardDescription className="text-xs">
                        Important information to ensure successful upload and modelling.
                    </CardDescription>
                </CardHeader>
                <CardContent className="pb-3">
                    <div className="grid gap-3 md:grid-cols-2 text-xs">
                        <div className="space-y-1 bg-background/50 p-2.5 rounded-lg border border-border/50">
                            <h4 className="font-semibold text-primary text-sm">GeoTIFF Uploads</h4>
                            <ul className="list-disc pl-4 space-y-0.5 text-muted-foreground">
                                <li>Must be projected in <span className="font-medium text-foreground">EPSG:4326</span> or <span className="font-medium text-foreground">UTM 35N</span>.</li>
                                <li>Maximum file size: <span className="font-medium text-foreground">500MB</span>.</li>
                                <li>Ensure raster bands are ordered correctly (e.g., <span className="font-medium text-foreground">B4, B3, B2, B8</span> for Sentinel-2).</li>
                            </ul>
                        </div>
                        <div className="space-y-1 bg-background/50 p-2.5 rounded-lg border border-border/50">
                            <h4 className="font-semibold text-primary text-sm">GPS &amp; Vector Data</h4>
                            <ul className="list-disc pl-4 space-y-0.5 text-muted-foreground">
                                <li>CSV files must explicitly contain <span className="font-medium text-foreground">'lat'</span> and <span className="font-medium text-foreground">'lon'</span> columns.</li>
                                <li>GeoJSON files must contain a <span className="font-medium text-foreground">FeatureCollection</span> of Polygons or Points.</li>
                                <li>Geometry must overlap with configured regions (AOI).</li>
                            </ul>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* ДОЛНИ ПАНЕЛИ: Форма за качване и Системен монитор — заема цялото оставащо пространство */}
            <div className="flex-1 min-h-0 grid gap-4 lg:grid-cols-5 px-4 pt-3">
                
                {/* РЪЧНО КАЧВАНЕ - ЛЯВА, ПО-ШИРОКА КОЛОНА */}
                <Card className="lg:col-span-3 shadow-md border-border/50 flex flex-col min-h-0">
                    <CardHeader className="flex-none bg-muted/20 border-b border-border/50 pb-2 pt-3">
                        <CardTitle className="flex items-center gap-2">
                            <Upload className="w-5 h-5" />
                            Manual Upload
                        </CardTitle>
                        <CardDescription>
                            Manually add Sentinel-2 GeoTIFF files, drone orthomosaics, or GPS logs.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="flex-1 min-h-0 overflow-y-auto space-y-3 pt-3 pb-3">
                        {/* Интерактивна зона за влачене и пускане (Drag and Drop) / Избор на файл */}
                        <div className="grid w-full items-center gap-1.5 focus-within:ring-2 focus-within:ring-primary/20 rounded-xl p-1 transition-all">
                            <Label htmlFor="data-file" className="px-1 text-xs font-semibold uppercase text-muted-foreground tracking-wider">Select files</Label>
                            <label
                                htmlFor="data-file"
                                className="flex flex-col items-center justify-center w-full h-28 border-2 border-dashed rounded-xl cursor-pointer bg-muted/20 hover:bg-muted/40 border-primary/20 hover:border-primary/50 transition-all duration-300"
                            >
                                <div className="flex flex-col items-center justify-center py-3">
                                    <div className="bg-primary/10 p-2 rounded-full mb-2">
                                        <Upload className="w-5 h-5 text-primary" />
                                    </div>
                                    <p className="mb-1 text-sm text-foreground text-center px-4">
                                        <span className="font-semibold text-primary hover:underline">Click here</span> or drag files here
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                        Supported: .TIF, .TIFF, .CSV, .GEOJSON
                                    </p>
                                </div>
                                <Input
                                    id="data-file"
                                    type="file"
                                    className="hidden"
                                    multiple // Позволява избор на множество файлове
                                    accept=".tif,.tiff,.csv,.geojson,.json"
                                    onChange={handleFileChange}
                                    disabled={uploading}
                                />
                            </label>
                        </div>

                        {/* Визуализация на избраните файлове */}
                        {files.length > 0 && (
                            <div className="space-y-2 max-h-32 overflow-y-auto pr-2 custom-scrollbar">
                                {files.map((file, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-2 bg-background rounded-lg border shadow-sm animate-in fade-in slide-in-from-bottom-2">
                                        <div className="flex items-center gap-3">
                                            <div className="bg-primary/10 p-1.5 rounded-md">
                                                <FileType className="h-4 w-4 text-primary" />
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-sm font-medium">{file.name}</span>
                                                {/* Показване на размера на файла в мегабайти */}
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

                        {/* Извеждане на съобщение за успех или грешка */}
                        {status && (
                            <div className={`p-3 rounded-lg flex items-center gap-3 text-sm font-medium animate-in fade-in zoom-in-95 ${
                                status.type === 'success' ? 'bg-green-500/10 text-green-600 border border-green-500/20' : 'bg-destructive/10 text-destructive border border-destructive/20'
                            }`}>
                                {status.type === 'success' ? (
                                    <CheckCircle2 className="h-4 w-4" />
                                ) : (
                                    <AlertCircle className="h-4 w-4" />
                                )}
                                {status.message}
                            </div>
                        )}

                        {/* Бутон за стартиране на същинското качване */}
                        <Button
                            size="lg"
                            className="w-full font-semibold"
                            disabled={files.length === 0 || uploading}
                            onClick={handleUpload}
                        >
                            {uploading ? (
                                <span className="flex items-center gap-2">
                                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent" />
                                    Processing upload...
                                </span>
                            ) : (
                                <>
                                    <Upload className="mr-2 h-4 w-4" />
                                    Start secure upload
                                </>
                            )}
                        </Button>
                    </CardContent>
                </Card>

                {/* СИСТЕМЕН МОНИТОР (За задачите) - ДЯСНА КОЛОНА */}
                <Card className="lg:col-span-2 shadow-md border-border/50 bg-gradient-to-br from-background to-muted/20 flex flex-col min-h-0">
                    <CardHeader className="flex-none bg-muted/20 border-b border-border/50 pb-2 pt-3">
                        <div className="flex items-center justify-between">
                            <CardTitle className="flex items-center gap-2">
                                <Activity className="h-5 w-5 text-primary" />
                                System Monitor
                            </CardTitle>
                            {/* Индикатор (пулсираща точка) за "На живо" */}
                            <span className="relative flex h-3 w-3">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                            </span>
                        </div>
                        <CardDescription>
                            Real-time tracking of active and recent pipeline tasks.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="p-0 flex-1 min-h-0">
                        <div className="p-3 h-full overflow-y-auto custom-scrollbar">
                            {/* Вграждане на компонента за следене на ETL задачите */}
                            <EtlMonitor />
                        </div>
                    </CardContent>
                </Card>

            </div>
        </div>
    );
}
