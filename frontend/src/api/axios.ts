import axios, { AxiosInstance, AxiosError } from 'axios';

// Create Axios instance
const api: AxiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Response interceptor to handle 401s
api.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
        if (error.response && error.response.status === 401) {
            console.warn('Unauthorized - 401. User session might be expired.');
        }
        return Promise.reject(error);
    }
);

export default api;
