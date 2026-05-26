import { create } from 'zustand';

// Интерфейс, дефиниращ структурата на едно известие (Notification)
export interface Notification {
    id: number; // Уникален идентификатор
    title: string; // Заглавие на известието
    message: string; // Детайлно съобщение
    type: 'alert' | 'info'; // Тип на известието - предупреждение или просто информация
    timestamp: string; // Време на създаване
    read: boolean; // Статус: прочетено или не
}

// Интерфейс за състоянието на хранилището (Zustand Store) за известия
interface NotificationStore {
    notifications: Notification[]; // Масив с всички известия
    unreadCount: number; // Брой на непрочетените известия
    addNotification: (notification: Omit<Notification, 'id' | 'read' | 'timestamp'>) => void; // Функция за добавяне на ново
    markAsRead: (id: number) => void; // Функция за маркиране на дадено известие като прочетено
    clearAll: () => void; // Изчистване на всички известия
}

// Създаване на глобален store за известия чрез Zustand
export const useNotifications = create<NotificationStore>((set) => ({
    // Първоначални тестови данни (mock data) за демонстрационни цели
    notifications: [
        {
            id: 1,
            title: 'Предупреждение: Спад в растителността',
            message: 'Засечен е драстичен спад в покритието (>20%) в района на Варненския залив.',
            type: 'alert',
            timestamp: new Date(Date.now() - 120000).toISOString(),
            read: false,
        },
        {
            id: 2,
            title: 'Обработена нова сцена',
            message: 'Сцената S2B_MSIL2A_20231215 от Sentinel-2 вече е налична.',
            type: 'info',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            read: false,
        }
    ],
    unreadCount: 2, // Начален брой на непрочетени известия

    // Метод за добавяне на ново известие в системата
    addNotification: (n) => set((state) => {
        // Формираме пълния обект, добавяйки автоматично генерирани полета (id, read, timestamp)
        const newN: Notification = {
            ...n,
            id: Date.now(), // Използваме текущото време като прост уникален идентификатор
            read: false,
            timestamp: new Date().toISOString(),
        };
        // Добавяме новото известие в началото на списъка
        const updated = [newN, ...state.notifications];
        return {
            notifications: updated,
            // Преизчисляваме броя на непрочетените известия
            unreadCount: updated.filter(i => !i.read).length
        };
    }),

    // Метод за маркиране на конкретно известие като прочетено
    markAsRead: (id) => set((state) => {
        // Намираме известието по ID и променяме флага 'read' на true
        const updated = state.notifications.map(n => n.id === id ? { ...n, read: true } : n);
        return {
            notifications: updated,
            // Преизчисляваме броя на непрочетените известия
            unreadCount: updated.filter(i => !i.read).length
        };
    }),

    // Метод за пълно изчистване на списъка с известия
    clearAll: () => set({ notifications: [], unreadCount: 0 }),
}));
