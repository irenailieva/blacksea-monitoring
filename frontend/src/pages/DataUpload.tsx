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
            setStatus({ type: 'success', message: 'Всички файлове са качени успешно!' });
            setFiles([]); // Изчистване на списъка
        } catch (error: any) {
            console.error('Грешка при качване:', error);
            
            // Обработка на съобщението за грешка, идващо от бекенда (FastAPI detail) или от мрежата
            let errorMsg = 'Възникна грешка при качването. Моля, опитайте отново.';
            if (error.response?.data?.detail) {
                errorMsg = `Грешка при качване: ${error.response.data.detail}`;
            } else if (error.message) {
                errorMsg = `Мрежова грешка: ${error.message}`;
            }
            setStatus({ type: 'error', message: errorMsg });
        } finally {
            setUploading(false); // Край на процеса по качване
        }
    };

    return (
        <div className="h-full overflow-y-auto pr-2">
            <div className="container mx-auto py-8 space-y-8">
                {/* Горен панел със заглавие и бутон за тригериране на ETL процес */}
                <div className="flex items-center justify-between p-1">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight text-primary">Качване на данни</h2>
                        <p className="text-muted-foreground mt-1 text-sm">Качване на локални данни или стартиране на автоматизиран Sentinel-2 процес.</p>
                    </div>
                    {/* Бутон за извикване на автоматизирания ETL (Extract, Transform, Load) процес */}
                    <Button 
                        size="lg"
                        className="shadow-md hover:shadow-lg transition-shadow"
                        onClick={async () => {
                            try {
                                // Изпращане на заявка за стартиране на фонова задача на сървъра
                                await api.post('/scenes/etl-trigger');
                                setStatus({ type: 'success', message: 'Автоматичният ETL процес стартира успешно!'});
                            } catch(e) {
                                setStatus({ type: 'error', message: 'Неуспешно стартиране на ETL процес.'});
                            }
                        }}
                    >
                        <Activity className="mr-2 h-4 w-4" /> 
                        Извличане от Sentinel-2
                    </Button>
                </div>

                {/* ИНФОРМАЦИОНЕН ПАНЕЛ (Указания) - ТОП, ХОРИЗОНТАЛЕН */}
                <Card className="w-full bg-primary/5 border-primary/10 shadow-sm">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-lg flex items-center gap-2">
                            <AlertCircle className="w-5 h-5 text-primary" />
                            Указания за обработка
                        </CardTitle>
                        <CardDescription>
                            Важна информация за гарантиране на успешното качване и моделиране.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid gap-6 md:grid-cols-2 text-sm">
                            <div className="space-y-3 bg-background/50 p-4 rounded-lg border border-border/50">
                                <h4 className="font-semibold text-primary">GeoTIFF Качвания</h4>
                                <ul className="list-disc pl-4 space-y-1.5 text-muted-foreground">
                                    <li>Трябва да са в проекция <span className="font-medium text-foreground">EPSG:4326</span> или <span className="font-medium text-foreground">UTM 35N</span>.</li>
                                    <li>Максимален размер на файла: <span className="font-medium text-foreground">500MB</span>.</li>
                                    <li>Уверете се, че растерните канали са подредени правилно (напр. <span className="font-medium text-foreground">B4, B3, B2, B8</span> за Sentinel-2).</li>
                                </ul>
                            </div>
                            <div className="space-y-3 bg-background/50 p-4 rounded-lg border border-border/50">
                                <h4 className="font-semibold text-primary">GPS & Векторни данни</h4>
                                <ul className="list-disc pl-4 space-y-1.5 text-muted-foreground">
                                    <li>CSV файловете трябва изрично да съдържат колони <span className="font-medium text-foreground">'lat'</span> и <span className="font-medium text-foreground">'lon'</span>.</li>
                                    <li>GeoJSON файловете трябва да съдържат <span className="font-medium text-foreground">FeatureCollection</span> от тип Polygons или Points.</li>
                                    <li>Геометрията трябва да се припокрива с конфигурираните региони (AOI).</li>
                                </ul>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* ДОЛНИ ПАНЕЛИ: Форма за качване и Системен монитор */}
                <div className="grid gap-8 lg:grid-cols-5">
                    
                    {/* РЪЧНО КАЧВАНЕ - ЛЯВА, ПО-ШИРОКА КОЛОНА */}
                    <Card className="lg:col-span-3 shadow-md border-border/50">
                        <CardHeader className="bg-muted/20 border-b border-border/50 pb-4">
                            <CardTitle className="flex items-center gap-2">
                                <Upload className="w-5 h-5" />
                                Ръчно качване
                            </CardTitle>
                            <CardDescription>
                                Ръчно вмъкване на Sentinel-2 GeoTIFF файлове, ортофотопланове от дронове или GPS логове.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6 pt-6">
                            {/* Интерактивна зона за влачене и пускане (Drag and Drop) / Избор на файл */}
                            <div className="grid w-full items-center gap-1.5 focus-within:ring-2 focus-within:ring-primary/20 rounded-xl p-1 transition-all">
                                <Label htmlFor="data-file" className="px-1 text-xs font-semibold uppercase text-muted-foreground tracking-wider">Изберете файлове</Label>
                                <label
                                    htmlFor="data-file"
                                    className="flex flex-col items-center justify-center w-full h-40 border-2 border-dashed rounded-xl cursor-pointer bg-muted/20 hover:bg-muted/40 border-primary/20 hover:border-primary/50 transition-all duration-300"
                                >
                                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                        <div className="bg-primary/10 p-3 rounded-full mb-4">
                                            <Upload className="w-8 h-8 text-primary" />
                                        </div>
                                        <p className="mb-2 text-sm text-foreground text-center px-4">
                                            <span className="font-semibold text-primary hover:underline">Кликнете тук</span> или плъзнете файловете тук
                                        </p>
                                        <p className="text-xs text-muted-foreground">
                                            Поддържат се: .TIF, .TIFF, .CSV, .GEOJSON
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
                                <div className="space-y-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                                    {files.map((file, idx) => (
                                        <div key={idx} className="flex items-center justify-between p-3 bg-background rounded-lg border shadow-sm animate-in fade-in slide-in-from-bottom-2">
                                            <div className="flex items-center gap-3">
                                                <div className="bg-primary/10 p-2 rounded-md">
                                                    <FileType className="h-5 w-5 text-primary" />
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
                                        Качването се обработва...
                                    </span>
                                ) : (
                                    <>
                                        <Upload className="mr-2 h-4 w-4" />
                                        Започни сигурно качване
                                    </>
                                )}
                            </Button>
                        </CardContent>
                    </Card>

                    {/* СИСТЕМЕН МОНИТОР (За задачите) - ДЯСНА КОЛОНА */}
                    <Card className="lg:col-span-2 shadow-md border-border/50 bg-gradient-to-br from-background to-muted/20">
                        <CardHeader className="bg-muted/20 border-b border-border/50 pb-4">
                            <div className="flex items-center justify-between">
                                <CardTitle className="flex items-center gap-2">
                                    <Activity className="h-5 w-5 text-primary" />
                                    Системен монитор
                                </CardTitle>
                                {/* Индикатор (пулсираща точка) за "На живо" */}
                                <span className="relative flex h-3 w-3">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                                </span>
                            </div>
                            <CardDescription>
                                Проследяване в реално време на активните и скорошните процеси.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="p-0">
                            <div className="p-4 h-[400px] overflow-y-auto custom-scrollbar">
                                {/* Вграждане на компонента за следене на ETL задачите */}
                                <EtlMonitor />
                            </div>
                        </CardContent>
                    </Card>

                </div>
            </div>
        </div>
    );
}
