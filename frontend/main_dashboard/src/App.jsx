import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AdminLayout from './components/layout/AdminLayout';
import Dashboard from './pages/admin/Dashboard';
import Inventory from './pages/admin/Inventory';
import Chatbot from './pages/admin/Chatbot';
import Requisitions from './pages/admin/Requisitions';
import DataEntry from './pages/vendor/DataEntry';
import StaffRequisition from './pages/staff/StaffRequisition';
import Login from './pages/Login';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* ── Public Routes ─────────────────────────────────────── */}
          <Route path="/login" element={<Login />} />

          {/* Root redirect → login (auth will redirect to dashboard) */}
          <Route path="/" element={<Navigate to="/admin/dashboard" replace />} />

          {/* ── Protected: Vendor (staff+) ───────────────────────── */}
          <Route element={<ProtectedRoute requiredRole="staff" />}>
            <Route path="/vendor" element={<DataEntry />} />
          </Route>

          {/* ── Protected: Staff ─────────────────────────────────── */}
          <Route element={<ProtectedRoute requiredRole="staff" />}>
            <Route path="/staff" element={<StaffRequisition />} />
          </Route>

          {/* ── Protected: Admin / Manager (admin layout) ─────────── */}
          <Route element={<ProtectedRoute requiredRole="manager" />}>
            <Route path="/admin" element={<AdminLayout />}>
              <Route index element={<Navigate to="/admin/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="inventory" element={<Inventory />} />
              <Route path="requisitions" element={<Requisitions />} />
              <Route path="chat" element={<Chatbot />} />
            </Route>
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
