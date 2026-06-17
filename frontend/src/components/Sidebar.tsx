import { NavLink, useNavigate } from 'react-router-dom';
import { 
  ShieldAlert, LayoutDashboard, Activity, LogOut, Users, 
  Bell, Zap, Network, Crosshair
} from 'lucide-react';
import { useEffect, useState } from 'react';

export default function Sidebar() {
  const navigate = useNavigate();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const userData = localStorage.getItem('sentinelx_user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('sentinelx_token');
    localStorage.removeItem('sentinelx_user');
    navigate('/login');
  };

  const navClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-5 py-3 rounded-xl transition-all group border ${
      isActive
        ? 'bg-primary/10 text-primary font-bold uppercase tracking-widest text-sm border-primary/20 shadow-[0_0_15px_rgba(var(--primary-rgb),0.1)]'
        : 'text-muted-foreground hover:bg-muted hover:text-foreground font-bold uppercase tracking-widest text-sm border-transparent'
    }`;

  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col h-screen p-6 relative overflow-hidden transition-colors duration-300">
      <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-primary via-violet-500 to-transparent opacity-30" />
      
      <div className="flex items-center gap-3 px-2 py-6 mb-12 group cursor-pointer" onClick={() => navigate('/dashboard')}>
        <div className="relative">
          <div className="absolute inset-0 bg-primary/20 blur-lg rounded-full group-hover:bg-primary/40 transition-all" />
          <ShieldAlert className="text-primary w-8 h-8 relative z-10 group-hover:rotate-12 transition-transform duration-500" />
        </div>
        <div>
          <h1 className="text-xl font-extrabold tracking-tight leading-none uppercase">
            <span className="text-foreground">Sentinel</span>
            <span className="text-primary">X</span>
          </h1>
          <p className="text-sm font-bold uppercase tracking-[0.3em] text-muted-foreground mt-1">Security</p>
        </div>
      </div>

      <nav className="flex-1 space-y-2">
        <NavLink to="/dashboard" className={navClass}>
          <LayoutDashboard className="w-4 h-4 group-hover:scale-110 transition-transform" />
          Dashboard
        </NavLink>
        <NavLink to="/analyze" className={navClass}>
          <Activity className="w-4 h-4 group-hover:scale-110 transition-transform" />
          Threat Analysis
        </NavLink>
        <NavLink to="/alerts" className={navClass}>
          <Bell className="w-4 h-4 group-hover:scale-110 transition-transform" />
          Alerts
        </NavLink>
        <NavLink to="/graph" className={navClass}>
          <Network className="w-4 h-4 group-hover:scale-110 transition-transform" />
          Threat Graph
        </NavLink>
        <NavLink to="/redteam" className={navClass}>
          <Crosshair className="w-4 h-4 group-hover:scale-110 transition-transform" />
          Red Team Gen
        </NavLink>
        <NavLink to="/playbooks" className={navClass}>
          <Zap className="w-4 h-4 group-hover:scale-110 transition-transform" />
          Automated Responses
        </NavLink>
        
        {(user?.role === 'soc' || user?.role === 'sysadmin') && (
          <NavLink to="/organization" className={navClass}>
            <Users className="w-4 h-4 group-hover:scale-110 transition-transform" />
            Unit Directory
          </NavLink>
        )}
        
        <div className="pt-4 mt-4 border-t border-border">
          <a 
            href="https://phishing-educator.vercel.app/" 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center justify-between px-5 py-3 rounded-xl bg-gradient-to-r from-primary/20 to-violet-500/20 text-primary border border-primary/30 shadow-[0_0_15px_rgba(var(--primary-rgb),0.2)] hover:shadow-[0_0_25px_rgba(var(--primary-rgb),0.4)] hover:scale-[1.02] transition-all group"
          >
            <div className="flex items-center gap-3">
              <div className="p-1.5 bg-primary/20 rounded-lg group-hover:bg-primary/30 transition-colors">
                <ShieldAlert className="w-4 h-4 animate-pulse" />
              </div>
              <span className="font-bold uppercase tracking-widest text-[10px]">Learning Hub</span>
            </div>
            <div className="w-2 h-2 rounded-full bg-primary animate-ping" />
          </a>
        </div>
      </nav>

      <div className="mt-auto space-y-4">
        {user && (
          <div className="px-4 py-4 bg-muted/50 rounded-2xl border border-border relative overflow-hidden group">
            <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="flex items-center gap-3 relative z-10">
              <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-bold text-sm uppercase shadow-inner">
                {user.name.charAt(0)}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-bold text-foreground uppercase tracking-wider truncate">{user.name}</p>
                <p className="text-sm text-muted-foreground font-bold uppercase tracking-widest mt-0.5">{user.role}</p>
              </div>
            </div>
          </div>
        )}

        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-5 py-3.5 rounded-xl text-muted-foreground hover:bg-red-500/10 hover:text-red-500 transition-all w-full font-bold uppercase tracking-widest text-sm border border-transparent hover:border-red-500/10"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
  );
}
