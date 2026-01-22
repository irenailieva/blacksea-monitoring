import { create } from 'zustand';
import api from '../api/axios';
import { User } from '../api/types';
import { AxiosError } from 'axios';

interface AuthState {
    user: User | null;
    isLoading: boolean;
    error: string | null;
    loginWithCredentials: (formData: FormData) => Promise<void>;
    register: (userData: any) => Promise<void>;
    logout: () => Promise<void>;
    checkAuth: () => Promise<void>;
}

const useAuth = create<AuthState>((set) => ({
    user: null,
    isLoading: true,
    error: null,

    loginWithCredentials: async (formData: FormData) => {
        set({ isLoading: true, error: null });
        try {
            const data = Object.fromEntries(formData.entries());
            await api.post('/auth/login', { ...data, set_cookie: true });

            const userResponse = await api.get<User>('/auth/me');
            set({ user: userResponse.data, isLoading: false });
        } catch (err) {
            console.error('Login failed', err);
            let msg = 'Login failed';
            if (err instanceof AxiosError && err.response) {
                if (err.response.status === 401) msg = 'Invalid email or password';
                else msg = (err.response.data as any)?.detail || 'Server error';
            }
            set({ error: msg, isLoading: false });
            throw err;
        }
    },

    register: async (userData: any) => {
        set({ isLoading: true, error: null });
        try {
            await api.post('/auth/register', userData);
            set({ isLoading: false });
        } catch (err) {
            console.error('Registration failed', err);
            let msg = 'Registration failed';
            if (err instanceof AxiosError && err.response) {
                msg = (err.response.data as any)?.detail || 'Server error';
            }
            set({ error: msg, isLoading: false });
            throw err;
        }
    },

    logout: async () => {
        set({ isLoading: true });
        try {
            // await api.post('/auth/logout'); 
        } catch (e) {
            console.warn('Logout error', e);
        } finally {
            set({ user: null, isLoading: false, error: null });
        }
    },

    checkAuth: async () => {
        set({ isLoading: true });
        try {
            const response = await api.get<User>('/auth/me');
            set({ user: response.data, isLoading: false });
        } catch (err) {
            set({ user: null, isLoading: false });
        }
    },
}));

export default useAuth;
