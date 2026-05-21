import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from './store/authStore';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import CostingSheetDetail from './pages/CostingSheetDetail';
import ExportsHistory from './pages/ExportsHistory';
import Settings from './pages/Settings';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) {
    console.log('[ProtectedRoute] NOT authenticated — redirecting to /login');
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

const queryClient = new QueryClient();

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/sheets/:sheetId" element={<ProtectedRoute><CostingSheetDetail /></ProtectedRoute>} />
          <Route path="/sheets/:sheetId/exports" element={<ProtectedRoute><ExportsHistory /></ProtectedRoute>} />
          <Route path="/exports" element={<ProtectedRoute><ExportsHistory /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
