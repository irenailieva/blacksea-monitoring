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
import Settings from './pages/Settings';
import './App.css';

// Requires authentication
interface RequireAuthProps {
  children: ReactNode;
}

function RequireAuth({ children }: RequireAuthProps) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return <>{children}</>;
}

// Requires one of the specified roles — redirects to / otherwise
interface RequireRoleProps {
  children: ReactNode;
  roles: string[];
}

function RequireRole({ children, roles }: RequireRoleProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) return <div>Loading...</div>;
  if (!user || !roles.includes(user.role)) return <Navigate to="/" replace />;
  return <>{children}</>;
}


function App() {
  const { checkAuth } = useAuth();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected Dashboard Routes */}
        <Route
          path="/"
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="analysis" element={<Analysis />} />
          <Route path="data" element={
            <RequireRole roles={['researcher', 'admin']}>
              <DataUpload />
            </RequireRole>
          } />
          <Route path="admin" element={<TeamManagement />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
