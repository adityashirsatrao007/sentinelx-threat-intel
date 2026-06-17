import { useState, useEffect, useRef } from 'react';
import { 
  Smartphone, ShieldAlert, Zap, Lock,
  MessageSquare, ShieldCheck,
  User, ArrowLeft
} from 'lucide-react';
import api from '../lib/api';

export default function MobileRemote() {
  const [mode, setMode] = useState<'controller' | 'victim'>('victim');
  const [, setLoading] = useState<string | null>(null);
  const [, setSuccess] = useState<string | null>(null);
  
  // Victim State
  const [incoming, setIncoming] = useState<any>(null);
  const [intercepting, setIntercepting] = useState(false);
  const [blocked, setBlocked] = useState(false);
  const lastId = useRef(0);

  useEffect(() => {
    const poll = async () => {
      try {
        const resp = await api.get(`/remote/events?since_id=${lastId.current}`);
        if (resp.data.length > 0) {
          lastId.current = resp.data[resp.data.length - 1].id;
          const attack = resp.data.find((e: any) => e.event_type === 'MOBILE_ATTACK');
          if (attack) {
            setIncoming(attack.payload);
            setIntercepting(true);
            setBlocked(false);
            
            // Sequence the "Blocking" animation
            setTimeout(() => {
              setIntercepting(false);
              setBlocked(true);
            }, 3000);
          }
        }
      } catch (err) {
        console.error(err);
      }
    };

    const interval = setInterval(poll, 1500);
    return () => clearInterval(interval);
  }, []);

  const triggerEvent = async (type: string, payload: any = {}) => {
    setLoading(type);
    try {
      await api.post('/remote/event', { type, payload });
      setSuccess(type);
      setTimeout(() => setSuccess(null), 2000);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(null);
    }
  };

  if (mode === 'victim') {
    return (
      <div className="min-h-screen bg-[#0a0a0a] text-white p-4 font-sans flex flex-col">
        {/* iOS-style Header */}
        <div className="flex justify-between items-center py-4 mb-4">
          <h1 className="text-2xl font-bold">Messages</h1>
          <button 
            onClick={() => setMode('controller')}
            className="text-xs font-bold uppercase tracking-widest text-primary bg-primary/10 px-3 py-1.5 rounded-full"
          >
            Switch to Remote
          </button>
        </div>

        {/* Message List */}
        <div className="flex-1 space-y-4">
          <div className="flex items-center gap-4 bg-[#1c1c1e] p-4 rounded-2xl border border-white/5 opacity-50">
            <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center">
              <User className="w-6 h-6" />
            </div>
            <div>
              <p className="font-bold">Mom</p>
              <p className="text-sm text-gray-400">See you for dinner at 7!</p>
            </div>
          </div>

          <div className="flex items-center gap-4 bg-[#1c1c1e] p-4 rounded-2xl border border-white/5 opacity-50">
            <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
              <User className="w-6 h-6" />
            </div>
            <div>
              <p className="font-bold">Work (Slack)</p>
              <p className="text-sm text-gray-400">The meeting has been moved.</p>
            </div>
          </div>

          {/* Incoming Attack */}
          {incoming && (
            <div className={`relative transition-all duration-500 transform ${intercepting ? 'scale-105' : 'scale-100'}`}>
              <div className={`flex items-start gap-4 p-4 rounded-2xl border transition-all duration-500 ${
                blocked ? 'bg-red-500/10 border-red-500/30' : 'bg-[#1c1c1e] border-white/10'
              }`}>
                <div className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 ${
                  blocked ? 'bg-red-500' : 'bg-gray-500'
                }`}>
                  <ShieldAlert className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between items-start mb-1">
                    <p className="font-bold truncate">{incoming.sender}</p>
                    <span className="text-[10px] text-gray-500">Just now</span>
                  </div>
                  <p className={`text-sm leading-relaxed ${blocked ? 'line-through text-gray-500' : 'text-gray-300'}`}>
                    {incoming.subject ? `Subject: ${incoming.subject}\n` : ''}
                    {incoming.body || incoming.message}
                  </p>
                </div>
              </div>

              {/* Interception Overlay */}
              {intercepting && (
                <div className="absolute inset-0 bg-primary/20 backdrop-blur-sm rounded-2xl flex flex-col items-center justify-center border border-primary/50 animate-pulse">
                  <div className="bg-primary p-3 rounded-full mb-3 shadow-[0_0_20px_rgba(37,99,235,0.5)]">
                    <Zap className="w-6 h-6 text-white animate-bounce" />
                  </div>
                  <p className="text-sm font-bold uppercase tracking-[0.2em] text-primary">SentinelX Intercepting...</p>
                </div>
              )}

              {/* Blocked Badge */}
              {blocked && (
                <div className="absolute top-2 right-2 flex items-center gap-1.5 px-2.5 py-1 bg-red-500 rounded-full shadow-lg shadow-red-500/20 animate-bounce">
                  <ShieldCheck className="w-3 h-3 text-white" />
                  <span className="text-[10px] font-black uppercase tracking-tighter">PHISHING BLOCKED</span>
                </div>
              )}
            </div>
          )}

          {!incoming && (
            <div className="py-20 text-center opacity-30">
              <MessageSquare className="w-12 h-12 mx-auto mb-4" />
              <p className="text-sm font-medium uppercase tracking-widest">Awaiting incoming data...</p>
            </div>
          )}
        </div>

        {/* SentinelX Bottom Guard */}
        <div className="mt-auto py-6 border-t border-white/5">
          <div className="flex items-center justify-center gap-3 bg-emerald-500/5 border border-emerald-500/10 p-4 rounded-2xl">
            <ShieldCheck className="w-5 h-5 text-emerald-500" />
            <p className="text-xs font-bold uppercase tracking-widest text-emerald-500/80">
              SentinelX Endpoint Protection Active
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6 font-sans">
      <div className="max-w-md mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-primary/20 rounded-2xl border border-primary/30">
              <Smartphone className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold uppercase tracking-wider">SentinelX Remote</h1>
              <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Mobile Controller</p>
            </div>
          </div>
          <button 
            onClick={() => setMode('victim')}
            className="p-2.5 bg-slate-900 rounded-xl border border-slate-800"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
        </div>

        <div className="grid grid-cols-1 gap-6">
          {/* Controllers remain the same */}
          <div className="bg-slate-900/50 border border-primary/20 rounded-3xl p-6">
            <h2 className="text-sm font-bold uppercase tracking-widest text-primary mb-4 flex items-center gap-2">
              <Lock className="w-4 h-4" /> SOC Command
            </h2>
            <div className="grid grid-cols-1 gap-3">
              <button
                onClick={() => triggerEvent('NAVIGATE', { to: 'dashboard' })}
                className="w-full py-4 bg-slate-800 hover:bg-slate-700 rounded-xl font-bold uppercase tracking-widest text-xs border border-slate-700"
              >
                Go to Dashboard
              </button>
              <button
                onClick={() => triggerEvent('NAVIGATE', { to: 'alerts' })}
                className="w-full py-4 bg-slate-800 hover:bg-slate-700 rounded-xl font-bold uppercase tracking-widest text-xs border border-slate-700"
              >
                Go to Alerts
              </button>
              <button
                onClick={() => triggerEvent('PANIC_LOCK')}
                className="w-full py-4 bg-red-500/20 hover:bg-red-500/30 text-red-500 rounded-xl font-bold uppercase tracking-widest text-xs border border-red-500/30"
              >
                EMERGENCY LOCKDOWN
              </button>
            </div>
          </div>

          <div className="bg-slate-900/50 border border-orange-500/20 rounded-3xl p-6">
            <h2 className="text-sm font-bold uppercase tracking-widest text-orange-500 mb-4 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4" /> Attack Simulator
            </h2>
            <div className="grid grid-cols-1 gap-3">
              <button
                onClick={() => triggerEvent('MOBILE_ATTACK', { 
                  sender: '+1 (555) 019-2342', 
                  message: 'URGENT: Your account has been suspended. Please verify your identity at http://sentinelx-verify.com/login to restore access.' 
                })}
                className="w-full py-4 bg-orange-500/10 hover:bg-orange-500/20 text-orange-500 rounded-xl font-bold uppercase tracking-widest text-xs border border-orange-500/20"
              >
                Simulate SMS Phishing
              </button>
              <button
                onClick={() => triggerEvent('MOBILE_ATTACK', { 
                  sender: 'WhatsApp Security', 
                  message: 'Your verification code is 482-931. If you did not request this, click here: http://wa-security.net/auth' 
                })}
                className="w-full py-4 bg-orange-500/10 hover:bg-orange-500/20 text-orange-500 rounded-xl font-bold uppercase tracking-widest text-xs border border-orange-500/20"
              >
                Simulate WhatsApp Scam
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
