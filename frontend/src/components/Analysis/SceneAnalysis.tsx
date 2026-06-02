import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';
import api from '@/api/axios';
import { Scene } from '@/api/types';

// Свойства на компонента, очаква се обект от тип Scene (сателитна снимка)
interface SceneAnalysisProps {
    scene: Scene;
}

// Компонент за анализ на конкретна сателитна сцена (изчисляване на статистика)
export function SceneAnalysis({ scene }: SceneAnalysisProps) {
    // Състояние за управление на индикатора за зареждане
    const [loading, setLoading] = useState(false);
    
    // Състояние за съхранение на изчислените статистически данни
    const [stats, setStats] = useState({
        total_vegetation_area_m2: 0, // Обща площ на растителността
        vegetation_trend_percent: 0, // Тенденция спрямо предходната сцена (в %)
        avg_confidence: 0, // Средна увереност на ML модела при класификацията
        confidence_trend_percent: 0, // Промяна в увереността
        active_anomalies: 0, // Брой засечени аномалии (напр. рязък спад)
        anomalies_trend: 0 // Тенденция на аномалиите
    });

    // Използваме useEffect за зареждане на данните при промяна на подадената сцена
    useEffect(() => {
        if (!scene) return; // Ако няма избрана сцена, не правим нищо
        
        // Асинхронна функция за извличане на статистиката от бекенда
        const fetchStats = async () => {
            setLoading(true); // Активираме индикатора за зареждане
            try {
                // Изпращане на GET заявка до /analysis/stats с параметър scene_id
                const response = await api.get('/analysis/stats', {
                    params: { scene_id: scene.id }
                });
                // Записваме получените данни в състоянието
                setStats(response.data);
            } catch (error) {
                console.error('Failed to fetch scene statistics:', error);
            } finally {
                setLoading(false); // Деактивираме индикатора за зареждане
            }
        };
        fetchStats();
    }, [scene]); // Зависимост от scene - изпълнява се при всяка промяна

    // Ако данните се зареждат, показваме въртяща се иконка
    if (loading) {
        return (
            <div className="flex h-32 items-center justify-center col-span-full">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    // Рендиране на интерфейса с получената статистика
    return (
        // Грид система (мрежа) с 3 колони за големи екрани
        <div className="grid gap-4 md:grid-cols-3">
            {/* Карточка 1: Обща площ на растителността */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Vegetation Area</CardTitle>
                </CardHeader>
                <CardContent>
                    {/* Конвертираме квадратни метри в квадратни километри и форматираме числото */}
                    <div className="text-2xl font-bold">{(stats.total_vegetation_area_m2 / 1_000_000).toLocaleString(undefined, { maximumFractionDigits: 2 })} km²</div>
                    <p className="text-xs text-muted-foreground">
                        {stats.vegetation_trend_percent > 0 ? '+' : ''}{stats.vegetation_trend_percent}% vs previous scene
                    </p>
                </CardContent>
            </Card>
            
            {/* Карточка 2: Средна увереност на модела */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Avg. Confidence</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{stats.avg_confidence}%</div>
                    <p className="text-xs text-muted-foreground">
                        {stats.confidence_trend_percent > 0 ? '+' : ''}{stats.confidence_trend_percent}% vs previous scene
                    </p>
                </CardContent>
            </Card>
            
            {/* Карточка 3: Активни аномалии */}
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Active Anomalies</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-2xl font-bold">{stats.active_anomalies}</div>
                    <p className="text-xs text-muted-foreground">
                        {stats.anomalies_trend > 0 ? '+' : ''}{stats.anomalies_trend} new anomalies
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}
