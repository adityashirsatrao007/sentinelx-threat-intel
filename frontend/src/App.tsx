import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Analyze from './pages/Analyze';
import Alerts from './pages/Alerts';
import Organization from './pages/Organization';
import Playbooks from './pages/Playbooks';
import ThreatGraph from './pages/ThreatGraph';
import RedTeam from './pages/RedTeam';
import MobileRemote from './pages/MobileRemote';
import RemoteSync from './components/RemoteSync';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('sentinelx_token');
  if (!token) return <Navigate to="/login" replace />;
  return (
    <div className="flex h-screen w-full bg-background">
      <RemoteSync />
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
};

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        {/* Protected Routes */}
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/analyze" element={<ProtectedRoute><Analyze /></ProtectedRoute>} />
        <Route path="/alerts" element={<ProtectedRoute><Alerts /></ProtectedRoute>} />
        <Route path="/graph" element={<ProtectedRoute><ThreatGraph /></ProtectedRoute>} />
        <Route path="/redteam" element={<ProtectedRoute><RedTeam /></ProtectedRoute>} />
        <Route path="/organization" element={<ProtectedRoute><Organization /></ProtectedRoute>} />
        <Route path="/playbooks" element={<ProtectedRoute><Playbooks /></ProtectedRoute>} />
      </Routes>
      <Routes>
        <Route path="/mobile-remote" element={<MobileRemote />} />
      </Routes>
    </BrowserRouter>
  );
}
