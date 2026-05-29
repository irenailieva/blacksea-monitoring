import { useEffect, useState } from 'react';
import { VegetationChart } from '@/components/Analysis/VegetationChart';
import { ShapExplanation } from '@/components/Analysis/ShapExplanation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from '@/components/ui/button';
import { Download, Loader2 } from 'lucide-react';
import api from '@/api/axios';
import { Region } from '@/api/types';

// Форматира читаемо име за регион: AOI_27.810_43.119 -> "AOI 27.810°E, 43.119°N"
function formatRegionName(name: string): string {
    if (!name.startsWith('AOI_')) return name;
    const parts = name.replace('AOI_', '').split('_');
    if (parts.length >= 2) {
        const lon = parseFloat(parts[0]).toFixed(3);
        const lat = parseFloat(parts[1]).toFixed(3);
        return `AOI  ${lon}°E, ${lat}°N`;
    }
    return name;
}

export default function Analysis() {
    // Състояния на компонента
    const [selectedRegion, setSelectedRegion] = useState<string>(''); // Избран регион за анализ
    const [regions, setRegions] = useState<Region[]>([]); // Списък с наличните региони
    const [loading, setLoading] = useState(true); // Флаг за първоначално зареждане
    
    // Състояние за статистическите данни на избрания регион
    const [stats, setStats] = useState({
        total_vegetation_area_m2: 0,
        vegetation_trend_percent: 0,
        avg_confidence: 0,
        confidence_trend_percent: 0,
        active_anomalies: 0,
        anomalies_trend: 0
    });

    // Извличане на списъка с региони при първоначалното зареждане на компонента
    useEffect(() => {
        const fetchRegions = async () => {
            try {
                const response = await api.get<Region[]>('/regions');
                // Показваме всички региони — включително динамично генерираните AOI региони,
                // защото именно те съдържат обработените сцени.
                // Предефинираните (именувани) региони се показват първи.
                const named = response.data.filter(r => !r.name.startsWith('AOI_'));
                const aois  = response.data.filter(r =>  r.name.startsWith('AOI_'));
                const ordered = [...named, ...aois];
                setRegions(ordered);
                // Автоматично избиране: предпочитаме регион с вече обработени сцени.
                // Падаме обратно на първия наличен регион, ако няма такъв.
                const firstWithData = aois[0] ?? ordered[0];
                if (firstWithData) {
                    setSelectedRegion(firstWithData.id.toString());
                }
            } catch (error) {
                console.error('Неуспешно извличане на регионите:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchRegions();
    }, []);


    // Извличане на статистическите данни при промяна на избрания регион
    useEffect(() => {
        if (!selectedRegion) return; // Защита: ако няма избран регион, не правим заявка
        const fetchStats = async () => {
            try {
                // Изпращане на заявка към агрегиращия ендпойнт /analysis/stats
                const response = await api.get('/analysis/stats', {
                    params: { region_id: selectedRegion }
                });
                setStats(response.data);
            } catch (error) {
                console.error('Неуспешно извличане на статистика:', error);
            }
        };
        fetchStats();
    }, [selectedRegion]); // Зависимост: изпълнява се при всяка промяна на selectedRegion

    // Визуализация по време на първоначалното зареждане
    if (loading) {
        return (
            <div className="flex h-full items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    // Функция за генериране и изтегляне на CSV файл с аналитичния репорт
    const exportAnalysisCSV = () => {
        // Намиране на името на текущо избрания регион
        const regionName = regions.find(r => r.id.toString() === selectedRegion)?.name || 'Неизвестен регион';
        
        // Дефиниране на заглавките на CSV файла
        const headers = ["Регион", "Метрика", "Стойност", "Тенденция"];
        
        // Подготовка на редовете с данни
        const rows = [
            [regionName, "Обща площ растителност (km²)", (stats.total_vegetation_area_m2 / 1_000_000).toFixed(2), `${stats.vegetation_trend_percent > 0 ? '+' : ''}${stats.vegetation_trend_percent}%`],
            [regionName, "Средна увереност на модела (%)", stats.avg_confidence.toString(), `${stats.confidence_trend_percent > 0 ? '+' : ''}${stats.confidence_trend_percent}%`],
            [regionName, "Активни аномалии", stats.active_anomalies.toString(), `${stats.anomalies_trend > 0 ? '+' : ''}${stats.anomalies_trend}`]
        ];
        
        // Сглобяване на CSV съдържанието
        const csvContent = [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
        // Създаване на Blob обект от стринга
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        // Генериране на временен URL
        const url = URL.createObjectURL(blob);
        
        // Създаване на невидим линк и програмно "кликване" върху него за стартиране на изтеглянето
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `analysis_summary_${regionName.replace(/ /g, '_')}_${new Date().toISOString().split('T')[0]}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link); // Почистване на DOM
    };

    // Рендиране на основния потребителски интерфейс
    return (
        <div className="flex flex-col space-y-4 h-full overflow-y-auto pr-2">
            {/* Горен панел: Заглавие, избор на регион и бутон за експорт */}
            <div className="flex items-center justify-between space-y-2 p-1">
                <h2 className="text-3xl font-bold tracking-tight">Табло за Анализи</h2>
                <div className="flex items-center space-x-2">
                    {/* Падащо меню (Select) за избор на регион */}
                    <Select value={selectedRegion} onValueChange={setSelectedRegion}>
                        <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder="Изберете регион" />
                        </SelectTrigger>
                        <SelectContent>
                            {regions.map(region => (
                                <SelectItem key={region.id} value={region.id.toString()}>
                                    {formatRegionName(region.name)}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                    {/* Бутон за изтегляне на CSV */}
                    <Button size="icon" variant="outline" onClick={exportAnalysisCSV} title="Експортиране в CSV">
                        <Download className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            {/* Мрежа с основните числови индикатори (KPIs) */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {/* Карточка 1: Площ */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Обща площ на растителността</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{(stats.total_vegetation_area_m2 / 1_000_000).toLocaleString(undefined, { maximumFractionDigits: 2 })} km²</div>
                        <p className="text-xs text-muted-foreground">
                            {stats.vegetation_trend_percent > 0 ? '+' : ''}{stats.vegetation_trend_percent}% спрямо предишна сцена
                        </p>
                    </CardContent>
                </Card>
                
                {/* Карточка 2: Увереност */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Ср. увереност (Confidence)</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.avg_confidence}%</div>
                        <p className="text-xs text-muted-foreground">
                            {stats.confidence_trend_percent > 0 ? '+' : ''}{stats.confidence_trend_percent}% спрямо предишна сцена
                        </p>
                    </CardContent>
                </Card>
                
                {/* Карточка 3: Аномалии */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Активни аномалии</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.active_anomalies}</div>
                        <p className="text-xs text-muted-foreground">
                            {stats.anomalies_trend > 0 ? '+' : ''}{stats.anomalies_trend} нови аномалии
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Мрежа с графики */}
            <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-3">
                {/* Графика: Тенденция във времето (заема 2/3 от ширината) */}
                <VegetationChart regionId={selectedRegion ? Number(selectedRegion) : null} />
                {/* Графика: Обяснимост на модела (заема 1/3 от ширината) */}
                <ShapExplanation regionId={selectedRegion} />
            </div>
        </div>
    );
}
