import { useEffect, useState } from 'react';
import { ImageOverlay, useMap } from 'react-leaflet';
import proj4 from 'proj4';

// Инжектиране на proj4 глобално, тъй като georaster разчита на него за координатни трансформации
// @ts-ignore
window.proj4 = proj4;

// @ts-ignore
import parseGeoraster from 'georaster';
import api from '../../api/axios';

// Свойства на компонента: URL на GeoTIFF файла и ниво на прозрачност
interface ClassificationOverlayProps {
    url: string;
    opacity?: number;
}

// Компонент за изобразяване на резултатите от класификацията (GeoTIFF конвертиран в PNG) като слой върху Leaflet картата
export default function ClassificationOverlay({ url, opacity = 0.8 }: ClassificationOverlayProps) {
    const map = useMap(); // Вземане на инстанцията на Leaflet картата
    const [bounds, setBounds] = useState<[[number, number], [number, number]] | null>(null); // Географски граници на слоя
    const [pngUrl, setPngUrl] = useState<string | null>(null); // URL адрес към PNG визуализацията

    useEffect(() => {
        if (!url) return;

        let isActive = true; // Флаг за предотвратяване на memory leaks при демонтиране
        // Конструиране на пълния URL адрес към TIFF файла
        const tifUrl = url.startsWith('http') ? url : `${import.meta.env.VITE_API_URL}${url.startsWith('/') ? '' : '/'}${url}`;
        // Бекендът предоставя PNG версия на същия адрес (сменяме разширението)
        // Добавяме параметър 'v' (timestamp), за да избегнем кеширане от браузъра при евентуална преработка
        const currentPngUrl = tifUrl.replace('.tif', '.png') + `?v=${Date.now()}`;

        // Изтегляне на TIFF файла веднъж, САМО за да извлечем неговите географски граници (Bounds)
        api.get(tifUrl, { responseType: 'arraybuffer' })
            .then(res => res.data)
            .then(parseGeoraster) // Парсиране на GeoTIFF метаданните
            .then(georaster => {
                if (!isActive) return;
                
                // Извличане на границите от метаданните на файла
                const { xmin, ymin, xmax, ymax } = georaster;
                // Преобразуване в Leaflet формат: [ [юг, запад], [север, изток] ]
                const leafBounds: [[number, number], [number, number]] = [
                    [ymin, xmin],
                    [ymax, xmax]
                ];
                
                // Запазване в състоянието
                setBounds(leafBounds);
                setPngUrl(currentPngUrl);
                
                // Еднократно фокусиране и мащабиране (zoom) на картата към новия слой при зареждане
                map.fitBounds(leafBounds, { padding: [50, 50], animate: true });
            })
            .catch(err => console.error("💥 Failed to fetch layer bounds:", err));

        // Почистваща функция при демонтиране на компонента
        return () => {
            isActive = false;
        };
    }, [url, map]);

    // Ако границите или PNG линкът все още не са налични, не изобразяваме нищо
    if (!bounds || !pngUrl) return null;

    // Рендиране на стандартен Leaflet ImageOverlay с PNG изображението, позиционирано според извлечените граници
    return (
        <ImageOverlay
            url={pngUrl}
            bounds={bounds}
            opacity={opacity}
            zIndex={1000} // Слагаме висок z-index, за да е над базовите карти
        />
    );
}
