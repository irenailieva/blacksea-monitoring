import { create } from 'zustand';

export interface Notification {
    id: number;
    title: string;
    message: string;
    type: 'alert' | 'info';
    timestamp: string;
    read: boolean;
}

interface NotificationStore {
    notifications: Notification[];
    unreadCount: number;
    addNotification: (notification: Omit<Notification, 'id' | 'read' | 'timestamp'>) => void;
    markAsRead: (id: number) => void;
    clearAll: () => void;
}

export const useNotifications = create<NotificationStore>((set) => ({
    notifications: [
        {
            id: 1,
            title: 'Alert: Vegetation Drop',
            message: 'Drastic coverage decrease (>20%) detected in Varna Bay area.',
            type: 'alert',
            timestamp: new Date(Date.now() - 120000).toISOString(),
            read: false,
        },
        {
            id: 2,
            title: 'New Scene Processed',
            message: 'Sentinel-2 scene S2B_MSIL2A_20231215 is now available.',
            type: 'info',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            read: false,
        }
    ],
    unreadCount: 2,
    addNotification: (n) => set((state) => {
        const newN: Notification = {
            ...n,
            id: Date.now(),
            read: false,
            timestamp: new Date().toISOString(),
        };
        const updated = [newN, ...state.notifications];
        return {
            notifications: updated,
            unreadCount: updated.filter(i => !i.read).length
        };
    }),
    markAsRead: (id) => set((state) => {
        const updated = state.notifications.map(n => n.id === id ? { ...n, read: true } : n);
        return {
            notifications: updated,
            unreadCount: updated.filter(i => !i.read).length
        };
    }),
    clearAll: () => set({ notifications: [], unreadCount: 0 }),
}));
