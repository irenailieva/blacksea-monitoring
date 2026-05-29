import { useEffect, ReactNode } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import useAuth from './store/useAuth';
import Login from './pages/Login';
import Register from './pages/Register';
import Layout from '@/components/Layout';
import Dashboard from './pages/Dashboard';
import Analysis from './pages/Analysis';
import DataUpload from './pages/DataUpload';
import TeamManagement from './pages/TeamManagement';
import RegionManagement from './pages/RegionManagement';
import Settings from './pages/Settings';
import './App.css';

// Интерфейс, дефиниращ свойствата (props) за компонента RequireAuth
// Очакваме children (наследници) от тип ReactNode
interface RequireAuthProps {
  children: ReactNode;
}

// Компонент от по-висок ред (HOC), който защитава маршрутите, изискващи автентикация
// Ако потребителят не е влязъл в системата, той бива пренасочен към страницата за вход
function RequireAuth({ children }: RequireAuthProps) {
  // Извличаме текущия потребител и състоянието на зареждане от глобалния store (Zustand)
  const { user, isLoading } = useAuth();
  // Вземаме текущото местоположение, за да можем да върнем потребителя тук след успешен вход
  const location = useLocation();

  // Докато се проверява автентикацията, показваме индикатор за зареждане
  if (isLoading) return <div>Loading...</div>;
  
  // Ако няма валиден потребител, пренасочваме към /login и запазваме пътя, от който идва
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  
  // Ако автентикацията е успешна, рендираме защитените компоненти
  return <>{children}</>;
}

// Интерфейс за свойствата на компонента за ролеви достъп
interface RequireRoleProps {
  children: ReactNode;
  roles: string[]; // Списък от позволени роли (напр. 'admin', 'researcher')
}

// Компонент, който ограничава достъпа въз основа на ролята на потребителя
// Предотвратява достъпа на неоторизирани лица до специфични административни или изследователски страници
function RequireRole({ children, roles }: RequireRoleProps) {
  const { user, isLoading } = useAuth();

  // Изчакваме приключването на проверката за сесия
  if (isLoading) return <div>Loading...</div>;
  
  // Ако потребителят липсва или неговата роля не е сред позволените, го връщаме на началната страница
  if (!user || !roles.includes(user.role)) return <Navigate to="/" replace />;
  
  // Ако проверката е успешна, позволяваме достъп
  return <>{children}</>;
}

// Главен компонент на приложението, който конфигурира маршрутизацията (routing)
function App() {
  // Функция за проверка на валидността на потребителската сесия (например проверка на HttpOnly cookies)
  const { checkAuth } = useAuth();

  // Използваме useEffect, за да изпълним проверката при първоначалното зареждане на приложението
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    // Дефинираме маршрутизатора за браузъра
    <BrowserRouter>
      {/* Routes контейнер за всички пътища в приложението */}
      <Routes>
        {/* Публични маршрути */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Защитени маршрути, които изискват потребителят да бъде влязъл */}
        <Route
          path="/"
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          {/* Dashboard е маршрутът по подразбиране (index) */}
          <Route index element={<Dashboard />} />
          
          {/* Страница за анализ на данните от Sentinel-2 */}
          <Route path="analysis" element={<Analysis />} />
          
          {/* Страница за качване на данни, достъпна само за изследователи и администратори */}
          <Route path="data" element={
            <RequireRole roles={['researcher', 'admin']}>
              <DataUpload />
            </RequireRole>
          } />
          
          {/* Страница за управление на екипи (по подразбиране административен изглед, но в случая достъпен общо в този пример) */}
          <Route path="admin" element={<TeamManagement />} />
          
          {/* Управление на регионите (AOI) - строго само за администратори */}
          <Route path="regions" element={
            <RequireRole roles={['admin']}>
              <RegionManagement />
            </RequireRole>
          } />
          
          {/* Страница за потребителски настройки */}
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
