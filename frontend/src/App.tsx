import { useEffect, ReactNode } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import useAuth from './store/useAuth';
import Login from './pages/Login';
import Register from './pages/Register';
import Layout from '@/components/Layout';
import Dashboard from './pages/Dashboard';
import Analysis from './pages/Analysis';
import './App.css';

// Simple Protected Route wrapper
interface RequireAuthProps {
  children: ReactNode;
}

function RequireAuth({ children }: RequireAuthProps) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <div>Loading...</div>; // Or a proper loading spinner
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

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
            <div className="flex items-center justify-center h-full border-2 border-dashed border-gray-300 rounded-lg p-12 text-center text-gray-500">
              <h3 className="text-lg font-medium">Data Component Placeholder</h3>
            </div>
          } />
          <Route path="admin" element={
            <div className="flex items-center justify-center h-full border-2 border-dashed border-gray-300 rounded-lg p-12 text-center text-gray-500">
              <h3 className="text-lg font-medium">Admin Component Placeholder</h3>
            </div>
          } />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
