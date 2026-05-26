import axios, { AxiosInstance, AxiosError } from 'axios';

// Създаване на предварително конфигурирана инстанция на Axios за HTTP заявки
const api: AxiosInstance = axios.create({
    // Задаваме базовия URL адрес на нашия FastAPI бекенд
    // Използваме променлива на средата (VITE_API_URL) или връщаме към localhost за разработка
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    
    // КРИТИЧНО ЗА СИГУРНОСТТА: Позволява изпращането на HttpOnly бисквитки с всяка заявка
    // Тъй като не пазим JWT токена в LocalStorage заради XSS атаки, разчитаме на бисквитки.
    withCredentials: true,
    
    // По подразбиране очакваме и изпращаме JSON формат
    headers: {
        'Content-Type': 'application/json',
    },
});

// Добавяне на прихващач (interceptor) за отговорите от сървъра
api.interceptors.response.use(
    // Ако отговорът е успешен (статус код 2xx), го връщаме без промяна
    (response) => response,
    
    // Обработка на грешки (статус кодове извън 2xx)
    (error: AxiosError) => {
        // Проверяваме дали грешката е 401 Unauthorized (неоторизиран достъп)
        if (error.response && error.response.status === 401) {
            // Това обикновено означава, че JWT токенът е изтекъл или липсва
            console.warn('Неоторизиран достъп - 401. Потребителската сесия може да е изтекла.');
            // Тук би могло да се добави автоматично пренасочване към /login,
            // но в момента това се управлява от React компонентите (RequireAuth)
        }
        // Прехвърляме грешката нататък, за да бъде обработена от извикващата функция
        return Promise.reject(error);
    }
);

export default api;
