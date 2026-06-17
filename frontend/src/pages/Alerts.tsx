import { useEffect, useState, useCallback } from 'react';
import { 
  ShieldAlert, ShieldCheck, Clock, 
  CheckCircle2, AlertTriangle, AlertCircle, Info, Activity,
  ArrowRight, Bell, Ban, XCircle
} from 'lucide-react';
import api from '../lib/api';

interface Alert {
  id: string;
  severity: string;
  title: string;
  description: string;
  acknowledged: boolean;
  created_at: string;
  threat: {
    sender: string;
    risk_score: number;
    channel: string;
    content_excerpt: string;
  }
}

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'pending' | 'acknowledged'>('pending');
  const [actionedAlerts, setActionedAlerts] = useState<Record<string, string>>({});

  const handleQuickAction = (alertId: string, actionName: string) => {
    setActionedAlerts(prev => ({ ...prev, [alertId]: actionName }));
    setTimeout(() => {
      setActionedAlerts(prev => {
        const copy = { ...prev };
        delete copy[alertId];
        return copy;
      });
      // Automatically acknowledge after a quick action
      acknowledge(alertId);
    }, 2000);
  };


  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    try {
      const url = filter === 'all' 
        ? '/alerts' 
        : `/alerts?unacknowledged_only=${filter === 'pending'}`;
      const res = await api.get(url);
      setAlerts(res.data.alerts || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const acknowledge = async (id: string) => {
    try {
      await api.post(`/alerts/${id}/acknowledge`);
      if (filter === 'pending') {
        setAlerts(prev => prev.filter(a => a.id !== id));
      } else {
        setAlerts(prev => prev.map(a => a.id === id ? { ...a, acknowledged: true } : a));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const getSeverityIcon = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical': return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'high': return <AlertTriangle className="w-5 h-5 text-orange-500" />;
      default: return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getSeverityClass = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'critical': return 'bg-red-500/10 text-red-500 border-red-500/20';
      case 'high': return 'bg-orange-500/10 text-orange-500 border-orange-500/20';
      default: return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
    }
  };

  const stats = [
    { label: 'Pending', count: alerts.filter(a => !a.acknowledged).length, color: 'text-red-500' },
    { label: 'Critical', count: alerts.filter(a => a.severity === 'critical').length, color: 'text-red-600' },
    { label: 'Monitored', count: alerts.length, color: 'text-primary' },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto animate-fade-in transition-colors duration-300">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-8 mb-10">
        <div>
          <div className="flex items-center gap-2.5 text-red-500 mb-2.5">
            <Bell className="w-5 h-5 animate-bounce" />
            <span className="text-sm font-bold uppercase tracking-[0.3em]">Incidents</span>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight leading-none uppercase">Security <span className="text-muted-foreground/30">Alerts</span></h1>
          <p className="text-muted-foreground mt-4 max-w-lg font-medium leading-relaxed">Review and manage automated security alerts.</p>
        </div>
        <div className="flex bg-card border border-border p-1 rounded-xl shadow-sm">
          {(['pending', 'acknowledged', 'all'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`px-6 py-2 rounded-lg text-sm font-bold uppercase tracking-widest transition-all ${filter === t ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'text-muted-foreground hover:text-foreground'}`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Mini Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        {stats.map(s => (
          <div key={s.label} className="bg-card border border-border rounded-2xl p-6 flex items-center justify-between shadow-sm">
            <span className="text-sm font-bold uppercase text-muted-foreground tracking-widest">{s.label}</span>
            <span className={`text-2xl font-bold font-mono ${s.color}`}>{s.count}</span>
          </div>
        ))}
      </div>

      <div className="space-y-6">
        {loading ? (
          [...Array(4)].map((_, i) => (
            <div key={i} className="h-40 bg-card border border-border rounded-3xl animate-pulse" />
          ))
        ) : alerts.length === 0 ? (
          <div className="bg-card border border-border rounded-[40px] p-20 text-center relative overflow-hidden group shadow-sm">
            <div className="absolute inset-0 bg-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="w-20 h-20 bg-emerald-500/10 rounded-3xl flex items-center justify-center mx-auto mb-6 border border-emerald-500/20 rotate-3 group-hover:rotate-0 transition-transform shadow-inner">
              <ShieldCheck className="w-10 h-10 text-emerald-500" />
            </div>
            <h3 className="text-xl font-bold text-foreground uppercase tracking-widest mb-2">System is Safe</h3>
            <p className="text-muted-foreground text-sm max-w-xs mx-auto italic font-medium">No new security alerts need your attention right now.</p>
          </div>
        ) : (
          alerts.map((alert) => (
            <div 
              key={alert.id}
              className={`bg-card border border-border rounded-3xl p-8 hover:border-primary/20 transition-all relative overflow-hidden group shadow-sm ${alert.acknowledged ? 'opacity-50 grayscale-[0.5]' : ''}`}
            >
              {alert.severity === 'critical' && !alert.acknowledged && (
                <div className="absolute top-0 left-0 w-1.5 h-full bg-red-500 shadow-[2px_0_15px_rgba(239,68,68,0.3)]" />
              )}
              
              {!alert.acknowledged && (
                <div className="absolute inset-y-0 right-0 bg-card/95 backdrop-blur-md border-l border-border p-6 flex flex-col justify-center gap-3 translate-x-full group-hover:translate-x-0 transition-transform duration-300 ease-out shadow-[-10px_0_30px_rgba(0,0,0,0.05)] z-10 w-64">
                  {actionedAlerts[alert.id] ? (
                    <div className="flex flex-col items-center justify-center text-emerald-500 gap-3 h-full animate-fade-in">
                      <CheckCircle2 className="w-10 h-10 animate-bounce" />
                      <span className="text-sm font-bold uppercase tracking-widest text-center">{actionedAlerts[alert.id]} Executed</span>
                    </div>
                  ) : (
                    <>
                      <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-1 text-center">Quick Response</h4>
                      <button onClick={() => handleQuickAction(alert.id, 'Block')} className="flex items-center justify-center gap-2 w-full p-3 bg-red-500 hover:bg-red-600 text-white rounded-xl transition-colors font-bold uppercase tracking-wider text-xs shadow-md">
                        <Ban className="w-4 h-4" /> Block Origin
                      </button>
                      <button onClick={() => handleQuickAction(alert.id, 'Quarantine')} className="flex items-center justify-center gap-2 w-full p-3 bg-orange-500 hover:bg-orange-600 text-white rounded-xl transition-colors font-bold uppercase tracking-wider text-xs shadow-md">
                        <ShieldAlert className="w-4 h-4" /> Quarantine
                      </button>
                      <button onClick={() => handleQuickAction(alert.id, 'Ignore')} className="flex items-center justify-center gap-2 w-full p-3 bg-muted hover:bg-muted/80 text-foreground rounded-xl transition-colors font-bold uppercase tracking-wider text-xs">
                        <XCircle className="w-4 h-4" /> Dismiss
                      </button>
                    </>
                  )}
                </div>
              )}

              <div className="flex flex-col lg:flex-row lg:items-start gap-8">
                <div className={`p-5 rounded-2xl bg-background border border-border group-hover:border-primary/20 transition-all shadow-inner`}>
                  {getSeverityIcon(alert.severity)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-4 mb-4">
                    <span className={`text-sm font-bold uppercase tracking-widest px-3 py-1 rounded-lg border shadow-sm ${getSeverityClass(alert.severity)}`}>
                      {alert.severity}
                    </span>
                    <span className="text-muted-foreground/20">|</span>
                    <span className="text-sm font-bold text-muted-foreground/60 uppercase tracking-tight truncate max-w-[200px]">{alert.threat?.sender}</span>
                  </div>
                  
                  <h3 className="text-2xl font-bold text-foreground tracking-tight leading-tight mb-3 italic uppercase">{alert.title}</h3>
                  <p className="text-sm text-muted-foreground line-clamp-2 italic mb-6 font-medium leading-relaxed">"{alert.description}"</p>
                  
                  <div className="flex flex-wrap items-center gap-8 pt-6 border-t border-border">
                    <div className="flex items-center gap-2.5 text-sm font-bold uppercase text-muted-foreground/40 tracking-widest">
                      <Clock className="w-4 h-4" />
                      {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                    <div className="flex items-center gap-2.5 text-sm font-bold uppercase text-muted-foreground/40 tracking-widest">
                      <Activity className="w-4 h-4" />
                      Risk Score: <span className="text-foreground font-mono">{alert.threat?.risk_score}</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row lg:flex-col gap-3 min-w-[180px]">
                  {!alert.acknowledged ? (
                    <button
                      onClick={() => acknowledge(alert.id)}
                      className="bg-primary hover:bg-blue-600 text-white px-6 py-4 rounded-xl text-sm font-bold uppercase tracking-widest transition-all shadow-lg shadow-primary/10 flex items-center justify-center gap-3 group/btn"
                    >
                      Acknowledge
                      <ArrowRight className="w-4 h-4 group-hover/btn:translate-x-1 transition-transform" />
                    </button>
                  ) : (
                    <div className="flex items-center justify-center gap-2.5 text-emerald-500/60 text-sm font-bold uppercase tracking-widest italic px-6 py-4 bg-emerald-500/5 rounded-xl border border-emerald-500/10">
                      <CheckCircle2 className="w-4 h-4" />
                      Resolved
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
