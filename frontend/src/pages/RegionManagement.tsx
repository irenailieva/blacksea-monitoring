import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Plus, MoreHorizontal, Loader2, MapPin, Trash2 } from 'lucide-react';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter
} from "@/components/ui/dialog";
import api from '@/api/axios';
import { Region } from '@/api/types';

// Страница за управление на географски региони (Region Management)
// Позволява добавяне, преглед и изтриване на зони, които се наблюдават от системата.
export default function RegionManagement() {
    // Състояния за списъка с региони и потребителския интерфейс
    const [regions, setRegions] = useState<Region[]>([]); // Данни за всички региони
    const [loading, setLoading] = useState(true); // Флаг за първоначално зареждане
    const [isAddOpen, setIsAddOpen] = useState(false); // Управлява видимостта на модалния прозорец за добавяне
    
    // Състояния за формата за добавяне на нов регион
    const [newName, setNewName] = useState('');
    const [newDesc, setNewDesc] = useState('');
    const [newGeoJSON, setNewGeoJSON] = useState(''); // Стринг, съдържащ GeoJSON геометрията
    const [adding, setAdding] = useState(false); // Индикатор за протичаща заявка за добавяне
    const [errorMsg, setErrorMsg] = useState(''); // Съобщение за грешка при валидация или мрежови проблем

    // Функция за извличане на регионите от сървъра
    const fetchRegions = async () => {
        setLoading(true);
        try {
            const response = await api.get<Region[]>('/regions');
            // В отговора са включени както постоянните, така и временните (AOI_) региони.
            // Тук ги запазваме всички, за да бъдат показани в таблицата (с различни етикети).
            setRegions(response.data);
        } catch (error) {
            console.error('Неуспешно извличане на регионите:', error);
        } finally {
            setLoading(false);
        }
    };

    // Зареждане на данните при монтиране на компонента
    useEffect(() => {
        fetchRegions();
    }, []);

    // Обработчик за добавяне на нов регион
    const handleAddRegion = async () => {
        setAdding(true);
        setErrorMsg('');
        
        try {
            let geometry;
            // Валидация на въведения GeoJSON
            try {
                geometry = JSON.parse(newGeoJSON);
            } catch (e) {
                throw new Error("Невалиден JSON формат в полето за геометрия");
            }
            
            // Проверка дали типът на геометрията е съвместим
            if (geometry.type !== "Polygon" && geometry.type !== "MultiPolygon") {
                throw new Error("Геометрията трябва да бъде GeoJSON Polygon или MultiPolygon");
            }

            // Подготовка на данните за изпращане
            const payload = {
                name: newName,
                description: newDesc,
                area_km2: 100, // Фиктивна стойност за площта (в реална система се изчислява автоматично на бекенда чрез PostGIS)
                geometry: geometry
            };

            // POST заявка към API-то
            await api.post('/regions', payload);
            
            // При успех: затваряне на модала, опресняване на списъка и изчистване на формата
            setIsAddOpen(false);
            fetchRegions();
            setNewName('');
            setNewDesc('');
            setNewGeoJSON('');
        } catch (error: any) {
            console.error('Неуспешно добавяне на регион:', error);
            // Извеждане на конкретното съобщение за грешка
            setErrorMsg(error.message || error.response?.data?.detail || "Възникна грешка при добавянето на региона");
        } finally {
            setAdding(false);
        }
    };

    // Обработчик за изтриване на регион
    const handleDelete = async (id: number) => {
        // Потвърждение от потребителя преди необратимо действие
        if (!confirm("Сигурни ли сте, че искате да изтриете този регион?")) return;
        try {
            await api.delete(`/regions/${id}`);
            fetchRegions(); // Опресняване на таблицата след успешно изтриване
        } catch (error) {
            console.error('Неуспешно изтриване на регион:', error);
            alert("Неуспешно изтриване на регион");
        }
    };

    // Показване на индикатор по време на първоначалното зареждане
    if (loading && regions.length === 0) {
        return (
            <div className="flex h-full items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto pr-2">
            <div className="container mx-auto py-6 space-y-6">
                {/* Горен панел със заглавие и бутон за добавяне */}
                <div className="flex items-center justify-between p-1">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight">Управление на Региони</h2>
                        <p className="text-muted-foreground text-sm mt-1">
                            Управление на постоянните географски зони за мониторинг със Sentinel-2.
                        </p>
                    </div>
                    
                    {/* Модален прозорец (Dialog) за добавяне на нов регион */}
                    <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
                        <DialogTrigger asChild>
                            <Button>
                                <Plus className="mr-2 h-4 w-4" />
                                Добави Регион
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-[500px]">
                            <DialogHeader>
                                <DialogTitle>Добавяне на нов регион</DialogTitle>
                                <DialogDescription>
                                    Дефинирайте нова постоянна зона на интерес. Тя ще бъде автоматично добавена в таблото за анализи.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                                <div className="grid gap-2">
                                    <Label htmlFor="name">Име на региона</Label>
                                    <Input 
                                        id="name" 
                                        placeholder="напр. Крайбрежие Слънчев бряг" 
                                        value={newName} 
                                        onChange={e => setNewName(e.target.value)}
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label htmlFor="desc">Описание</Label>
                                    <Input 
                                        id="desc" 
                                        placeholder="Опционално описание" 
                                        value={newDesc} 
                                        onChange={e => setNewDesc(e.target.value)}
                                    />
                                </div>
                                <div className="grid gap-2">
                                    <Label htmlFor="geojson">GeoJSON Геометрия (Polygon)</Label>
                                    <Textarea 
                                        id="geojson" 
                                        placeholder='{"type": "Polygon", "coordinates": [[[...]]]}' 
                                        className="h-32 font-mono text-xs"
                                        value={newGeoJSON}
                                        onChange={e => setNewGeoJSON(e.target.value)}
                                    />
                                </div>
                                {/* Визуализация на грешка, ако има такава */}
                                {errorMsg && (
                                    <div className="text-sm text-destructive font-medium bg-destructive/10 p-2 rounded-md">
                                        {errorMsg}
                                    </div>
                                )}
                            </div>
                            <DialogFooter>
                                <Button variant="outline" onClick={() => setIsAddOpen(false)} disabled={adding}>Отказ</Button>
                                <Button onClick={handleAddRegion} disabled={adding || !newName || !newGeoJSON}>
                                    {adding ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                                    Запази Регион
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>

                {/* Таблица със съществуващите региони */}
                <Card>
                    <CardHeader>
                        <CardTitle>Конфигурирани региони</CardTitle>
                        <CardDescription>
                            Тези региони се картографират и проследяват активно от ETL пайплайна.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Регион</TableHead>
                                    <TableHead>Тип</TableHead>
                                    <TableHead>Детайли</TableHead>
                                    <TableHead className="text-right">Действия</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {regions.map((region) => (
                                    <TableRow key={region.id}>
                                        <TableCell>
                                            <div className="flex flex-col">
                                                <span className="font-medium flex items-center gap-2">
                                                    <MapPin className="h-4 w-4 text-primary" />
                                                    {region.name}
                                                </span>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            {/* Диференциране между временни (създадени от потребителски чертеж) и постоянни региони */}
                                            {region.name.startsWith("AOI_") || region.name.startsWith("aoi_") ? (
                                                <Badge variant="secondary">Временен AOI</Badge>
                                            ) : (
                                                <Badge variant="default" className="bg-green-600">Постоянен</Badge>
                                            )}
                                        </TableCell>
                                        <TableCell className="text-muted-foreground text-sm">
                                            ID: {region.id}
                                        </TableCell>
                                        <TableCell className="text-right">
                                            {/* Падащо меню с действия за конкретния регион */}
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" className="h-8 w-8 p-0">
                                                        <MoreHorizontal className="h-4 w-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuLabel>Действия</DropdownMenuLabel>
                                                    <DropdownMenuItem>Преглед на картата</DropdownMenuItem>
                                                    <DropdownMenuItem>Редактиране на геометрията</DropdownMenuItem>
                                                    <DropdownMenuSeparator />
                                                    <DropdownMenuItem className="text-destructive" onClick={() => handleDelete(region.id)}>
                                                        <Trash2 className="mr-2 h-4 w-4" />
                                                        Изтрий
                                                    </DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {/* Празно състояние, ако няма региони */}
                                {regions.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={4} className="text-center py-6 text-muted-foreground">
                                            Няма намерени региони. Добавете един, за да започнете.
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
