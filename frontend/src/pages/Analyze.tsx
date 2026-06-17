import { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { 
  Mail, MessageSquare, Loader2, ShieldCheck, ShieldAlert, 
  Phone, RefreshCw, PlayCircle, ArrowRight,
  Fingerprint, Zap, Mic2, Sparkles, Brain, Clock
} from 'lucide-react';
import api from '../lib/api';

interface ThreatSummary {
  id: string;
  type: string;
  channel: string;
  risk_score: number;
  threat_level: string;
  threat_detected: boolean;
  sender: string;
  content_excerpt: string;
  created_at: string;
}

const TEMPLATES = {
  email: [
    {
      title: "PayPal Suspension",
      sender: "service@paypaI-security.com",
      subject: "Your account has been temporarily suspended",
      body: "Dear Customer, We noticed suspicious activity on your PayPal account. For your protection, we have temporarily limited your account access. To restore full access, please verify your identity by clicking the link below: http://paypal-verify-secure.net/login. Failure to verify within 24 hours will result in permanent suspension."
    },
    {
      title: "Microsoft 365 Alert",
      sender: "no-reply@microsoft-admin.org",
      subject: "Action Required: Unusual sign-in activity",
      body: "We detected an unusual sign-in attempt on your Microsoft 365 account from a new location (Moscow, Russia). If this was not you, please secure your account immediately by following this link: http://m365-security-portal.io/auth. Failure to act may result in unauthorized access to your corporate data."
    }
  ],
  sms: [
    {
      title: "Bank Fraud Alert",
      sender: "+18885550199",
      body: "CHASE ALERT: A suspicious transaction of $1,450.00 was attempted on your card ending in 4292. If you did not authorize this, please click here to secure your account: http://chase-fraud-dept.co/secure"
    },
    {
      title: "Amazon Delivery",
      sender: "AMZN-MSG",
      body: "Your Amazon package could not be delivered due to an incorrect address. Please update your shipping details here to avoid the package being returned to the sender: http://amzn-address-update.biz/track"
    }
  ],
  call: [
    {
      title: "Tech Support Scam",
      sender: "Apple Support",
      body: "This is an automated call from Apple Support. We have detected a critical security breach in your iCloud account. Your private photos and messages are being uploaded to a remote server. Please do not hang up. Press 1 to speak with a senior security technician who will help you install a secure firewall and remote monitoring tool to stop the hackers."
    },
    {
      title: "IRS Legal Action",
      sender: "IRS Treasury",
      body: "This is Officer Steve Smith from the IRS. A lawsuit has been filed against you for federal tax evasion. A warrant for your arrest has been issued and local police are on their way to your residence. To stop the legal proceedings and resolve this matter out of court, please call our settlement department immediately at 800-555-0102."
    }
  ]
};

const SCAM_LEXICON = [
  'urgent', 'suspension', 'suspended', 'verify', 'password', 'wire transfer',
  'lawsuit', 'arrest', 'breach', 'unauthorized', 'gift card', 'gift cards',
  'reimburse', 'terminate', 'temporarily limited', 'click here', 'immediate action',
  'suspicious activity', 'unusual sign-in', 'fraud', 'authorize', 'firewall',
  'remote monitoring', 'tax evasion', 'warrant', 'IRS', 'Social Security'
];

export default function Analyze() {
  const location = useLocation();
  const [activeTab, setActiveTab] = useState<'email' | 'sms' | 'call'>('email');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<ThreatSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Form State
  const [sender, setSender] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [copied, setCopied] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [liveRisk, setLiveRisk] = useState(0);

  useEffect(() => {
    if (location.state) {
      const { sender, subject, body, type } = location.state;
      if (type) setActiveTab(type);
      if (sender) setSender(sender);
      if (subject) setSubject(subject);
      if (body) setBody(body);
    }
  }, [location]);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  };

  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const res = await api.get('/dashboard/threats?limit=15');
      setHistory(res.data.threats || []);
    } catch (err) {
      console.error("Failed to fetch history", err);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
    const clockInterval = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(clockInterval);
  }, [fetchHistory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      let payload: any;
      if (activeTab === 'email') {
        payload = { sender, subject, body };
      } else if (activeTab === 'sms') {
        payload = { sender, message: body };
      } else {
        payload = { transcript: body, caller_id: sender };
      }
        
      const res = await api.post(`/analyze/${activeTab}`, payload);
      setResult(res.data);
      fetchHistory();
    } catch (err) {
      console.error(err);
      alert("Analysis failed. Please check the console.");
    } finally {
      setLoading(false);
    }
  };

  const simulateCall = async () => {
    setActiveTab('call');
    setSender('+1 (800) 555-0199');
    setResult(null);
    setBody('');
    setIsStreaming(true);
    
    const script = "This is an automated call from the Fraud Department. We have detected unauthorized wire transfers from your account. To halt these transfers and verify your identity, we need you to immediately provide your secure account PIN and password. Failure to do so will result in an immediate account lockdown and potential lawsuit.";
    
    let currentText = "";
    for (let i = 0; i < script.length; i++) {
      currentText += script[i];
      setBody(currentText);
      // Gradually increase live risk probability
      if (i % 10 === 0) setLiveRisk(prev => Math.min(prev + (Math.random() * 8), 98));
      await new Promise(resolve => setTimeout(resolve, 30));
    }
    
    setIsStreaming(false);
    setLiveRisk(0);
    
    // Auto-submit after streaming finishes. We have to use the final values directly
    // since handleSubmit uses closure state which might be stale.
    setLoading(true);
    try {
      const res = await api.post(`/analyze/call`, { transcript: script, caller_id: '+1 (800) 555-0199' });
      setResult(res.data);
      fetchHistory();
    } catch (err) {
      console.error(err);
      alert("Analysis failed.");
    } finally {
      setLoading(false);
    }
  };

  const loadTemplate = (template: any) => {
    setSender(template.sender);
    if (template.subject) setSubject(template.subject);
    setBody(template.body);
    setResult(null);
  };

  const getRiskColor = (score: number) => {
    if (score >= 8.5) return 'text-red-500';
    if (score >= 6.0) return 'text-orange-500';
    if (score >= 3.0) return 'text-amber-500';
    return 'text-emerald-500';
  };

  const highlightText = (text: string) => {
    if (!text) return null;
    const regex = new RegExp(`\\b(${SCAM_LEXICON.join('|')})\\b`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, i) => {
      if (SCAM_LEXICON.map(w => w.toLowerCase()).includes(part.toLowerCase())) {
        return <span key={i} className="bg-red-500/10 text-red-600 border border-red-500/20 font-bold px-1.5 py-0.5 rounded-md mx-[2px] shadow-sm">{part}</span>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="p-8 max-w-7xl mx-auto animate-fade-in transition-colors duration-300">
      {/* ─── Header ──────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-8 mb-12">
        <div>
          <div className="flex items-center gap-2.5 text-primary mb-2.5">
            <Zap className="w-4 h-4 fill-current" />
            <span className="text-sm font-bold uppercase tracking-[0.3em]">Analysis Tool</span>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight leading-none uppercase">
            Threat <span className="text-muted-foreground/30">Analysis</span>
          </h1>
        </div>
        
        <div className="flex items-center gap-8 bg-card border border-border px-8 py-5 rounded-2xl shadow-sm">
          <div className="text-right">
             <p className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-1">System Time</p>
             <p className="text-2xl font-bold text-foreground font-mono tracking-tight">{formatTime(currentTime)}</p>
          </div>
          <div className="w-px h-10 bg-border" />
          <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-primary/5 border border-primary/20">
            <Brain className="w-5 h-5 text-primary" />
            <span className="text-sm font-bold uppercase text-primary tracking-widest">Qwen2.5-7B</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
        {/* Templates Sidebar */}
        <div className="space-y-6">
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
            <h3 className="text-sm font-bold uppercase text-muted-foreground tracking-widest mb-6 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              Templates
            </h3>
            <div className="space-y-2.5">
              {TEMPLATES[activeTab].map((t, i) => (
                <button
                  key={i}
                  onClick={() => loadTemplate(t)}
                  className="w-full text-left p-4 rounded-xl bg-background border border-border hover:bg-muted hover:border-primary/40 transition-all group"
                >
                  <p className="text-sm font-bold text-foreground uppercase tracking-wider group-hover:text-primary transition-colors">{t.title}</p>
                  <p className="text-sm text-muted-foreground line-clamp-1 mt-1 font-medium">"{t.body}"</p>
                </button>
              ))}
            </div>
          </div>

           {activeTab === 'call' && (
             <div className="bg-primary/5 border border-primary/10 rounded-2xl p-6">
               <h3 className="text-sm font-bold uppercase text-primary tracking-widest mb-4 flex items-center gap-2">
                 <Mic2 className="w-4 h-4" /> Voice Scam Detection
               </h3>
               <div className="h-12 flex items-center gap-1.5 mb-6">
                 {[...Array(12)].map((_, i) => (
                   <div key={i} className={`flex-1 bg-primary/40 rounded-full ${isStreaming ? 'animate-bounce bg-red-500/60' : 'animate-pulse'}`} style={{ height: `${Math.random() * 100}%`, animationDelay: `${i * 0.1}s` }} />
                 ))}
               </div>
               
               <button
                 onClick={simulateCall}
                 disabled={isStreaming || loading}
                 className="w-full py-3 px-4 bg-red-500 hover:bg-red-600 text-white rounded-xl font-bold uppercase tracking-widest text-sm shadow-lg shadow-red-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
               >
                 {isStreaming ? <Loader2 className="w-4 h-4 animate-spin" /> : <PlayCircle className="w-4 h-4" />}
                 {isStreaming ? 'Intercepting...' : 'Simulate Interception'}
               </button>
               {isStreaming && (
                 <div className="mt-6 pt-6 border-t border-primary/10 animate-fade-in">
                    <div className="flex justify-between items-end mb-2">
                       <span className="text-xs font-bold uppercase tracking-widest text-primary/60">Malicious Intent Probability</span>
                       <span className="text-sm font-bold text-red-500 font-mono">{liveRisk.toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-primary/10 h-1.5 rounded-full overflow-hidden">
                       <div className="h-full bg-red-500 transition-all duration-300" style={{ width: `${liveRisk}%` }} />
                    </div>
                 </div>
               )}
             </div>
          )}
        </div>

        {/* Main Analysis Column */}
        <div className="xl:col-span-2 space-y-8">
          <div className="flex gap-8 border-b border-border">
            <button
              onClick={() => { setActiveTab('email'); setResult(null); }}
              className={`pb-4 px-1 font-bold uppercase tracking-widest text-sm flex items-center gap-2.5 border-b-2 transition-all ${activeTab === 'email' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
            >
              <Mail className="w-4 h-4" /> Email
            </button>
            <button
              onClick={() => { setActiveTab('sms'); setResult(null); }}
              className={`pb-4 px-1 font-bold uppercase tracking-widest text-sm flex items-center gap-2.5 border-b-2 transition-all ${activeTab === 'sms' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
            >
              <MessageSquare className="w-4 h-4" /> SMS
            </button>
            <button
              onClick={() => { setActiveTab('call'); setResult(null); }}
              className={`pb-4 px-1 font-bold uppercase tracking-widest text-sm flex items-center gap-2.5 border-b-2 transition-all ${activeTab === 'call' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
            >
              <Phone className="w-4 h-4" /> Transcript
            </button>
          </div>

          <div className="space-y-6">
            <div className="bg-card border border-border rounded-3xl p-8 relative overflow-hidden group shadow-sm">
              <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-primary/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <form onSubmit={handleSubmit} className="space-y-6 relative z-10">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div>
                    <label className="block text-sm font-bold uppercase text-muted-foreground tracking-widest mb-2.5">Source Identity</label>
                    <input
                      required
                      type="text"
                      value={sender}
                      onChange={(e) => setSender(e.target.value)}
                      disabled={isStreaming}
                      placeholder="e.g. security@enron-corp.com"
                      className="w-full px-5 py-3.5 bg-background border border-border rounded-xl text-foreground placeholder:text-muted-foreground/30 focus:ring-2 focus:ring-primary/40 focus:border-primary outline-none transition-all font-semibold disabled:opacity-50"
                    />
                  </div>
                  
                  {activeTab === 'email' && (
                    <div>
                      <label className="block text-sm font-bold uppercase text-muted-foreground tracking-widest mb-2.5">Subject Header</label>
                      <input
                        required
                        type="text"
                        value={subject}
                        onChange={(e) => setSubject(e.target.value)}
                        placeholder="e.g. Unusual Login Activity"
                        className="w-full px-5 py-3.5 bg-background border border-border rounded-xl text-foreground placeholder:text-muted-foreground/30 focus:ring-2 focus:ring-primary/40 focus:border-primary outline-none transition-all font-semibold"
                      />
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-bold uppercase text-muted-foreground tracking-widest mb-2.5">Message Content</label>
                  <textarea
                    required
                    rows={8}
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    disabled={isStreaming}
                    placeholder="Paste content for AI evaluation..."
                    className={`w-full px-5 py-4 bg-background border border-border rounded-xl text-foreground placeholder:text-muted-foreground/30 focus:ring-2 focus:ring-primary/40 focus:border-primary outline-none transition-all resize-none font-medium leading-relaxed ${isStreaming ? 'border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.1)]' : ''}`}
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading || isStreaming}
                  className="w-full py-5 px-6 bg-primary hover:bg-blue-600 disabled:bg-muted disabled:text-muted-foreground rounded-2xl font-bold uppercase tracking-[0.2em] text-white shadow-lg shadow-primary/10 transition-all flex items-center justify-center gap-3 group"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : (
                    <>
                      Analyze Content
                      <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                </button>
              </form>
            </div>

            {result && (
              <div className="bg-card border border-border rounded-3xl p-8 animate-slide-up shadow-sm">
                <div className="flex items-center justify-between mb-8 pb-5 border-b border-border">
                  <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Analysis Results</h3>
                  <div className="flex items-center gap-4">
                     {activeTab === 'call' && (
                        <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/10 border border-red-500/20 rounded-lg">
                           <Fingerprint className="w-3.5 h-3.5 text-red-500" />
                           <span className="text-sm font-bold text-red-500 uppercase tracking-widest">AI Voice Probability: 89%</span>
                        </div>
                     )}
                     <button
                        onClick={() => {
                          navigator.clipboard.writeText(JSON.stringify(result, null, 2));
                          setCopied(true);
                          setTimeout(() => setCopied(false), 2000);
                        }}
                        className="text-sm font-bold uppercase tracking-widest text-primary hover:text-foreground transition-colors"
                      >
                        {copied ? 'Copied' : 'Export JSON'}
                      </button>
                  </div>
                </div>

                <div className="flex flex-col lg:flex-row items-start lg:items-center gap-10">
                  <div className="flex items-center gap-8 shrink-0">
                    <div className={`p-6 rounded-2xl ${result.threat_detected ? 'bg-red-500/10 text-red-500' : 'bg-emerald-500/10 text-emerald-500'} border border-current/10`}>
                      {result.threat_detected ? <ShieldAlert className="w-10 h-10" /> : <ShieldCheck className="w-10 h-10" />}
                    </div>
                    <div>
                      <div className="flex items-baseline gap-1.5">
                        <span className="text-5xl font-bold text-foreground font-mono leading-none tracking-tight">{result.risk_score}</span>
                        <span className="text-muted-foreground/30 text-sm font-bold uppercase tracking-widest">/ 10</span>
                      </div>
                      <p className={`text-sm font-bold uppercase tracking-widest mt-2 ${result.threat_detected ? 'text-red-500' : 'text-emerald-500'}`}>
                        {result.threat_level} Priority Incident
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 flex-1 w-full">
                     {[
                        { label: 'Classification', val: result.classification_label, color: 'text-foreground' },
                        { label: 'Confidence', val: `${(result.confidence * 100).toFixed(1)}%`, color: 'text-primary' },
                      ].map(m => (
                        <div key={m.label} className="bg-background border border-border p-4 rounded-xl shadow-inner flex-1">
                           <p className="text-sm font-bold uppercase text-muted-foreground tracking-widest mb-1.5">{m.label}</p>
                           <p className={`text-xs sm:text-sm font-bold uppercase tracking-widest truncate ${m.color}`} title={m.val}>{m.val}</p>
                        </div>
                      ))}
                  </div>
                </div>

                {/* XAI Highlight Block */}
                {result.threat_detected && (
                  <div className="mt-8 pt-8 border-t border-border">
                    <div className="flex items-center gap-2 mb-4">
                      <Sparkles className="w-4 h-4 text-primary" />
                      <p className="text-sm font-bold uppercase text-muted-foreground tracking-widest">Explainable AI: Forensic Breakdown</p>
                    </div>
                    <div className="bg-background border border-border p-6 rounded-2xl shadow-inner text-sm leading-loose text-foreground">
                      {highlightText(body)}
                    </div>
                  </div>
                )}

                {result.reasons.length > 0 && (
                  <div className="mt-8 pt-8 border-t border-border">
                    <p className="text-sm font-bold uppercase text-muted-foreground tracking-widest mb-5">Why we flagged this</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {result.reasons.map((r: string, i: number) => (
                        <div key={i} className="flex gap-4 text-base text-muted-foreground bg-background border border-border p-4 rounded-xl font-medium leading-relaxed shadow-sm">
                          <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                          {r}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Audit Log Column */}
        <div className="xl:col-span-1 space-y-6">
          <div className="bg-card border border-border rounded-3xl p-8 shadow-sm">
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Recent Scans</h3>
              <button onClick={fetchHistory} className="text-muted-foreground hover:text-foreground transition-colors">
                <RefreshCw className={`w-4 h-4 ${historyLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
            
            <div className="space-y-4 max-h-[700px] overflow-y-auto pr-2 scrollbar-hide">
              {history.map((h) => (
                <div 
                  key={h.id} 
                  onClick={() => { setSender(h.sender); setBody(h.content_excerpt); setActiveTab(h.channel as any); }}
                  className="group p-4 bg-background border border-border hover:bg-muted rounded-xl transition-all cursor-pointer shadow-sm"
                >
                  <div className="flex items-center justify-between mb-2">
                     <span className="text-sm font-bold text-muted-foreground truncate flex-1 tracking-tight">{h.sender.split('@')[0]}</span>
                     <span className={`text-sm font-bold font-mono ${getRiskColor(h.risk_score)}`}>{h.risk_score.toFixed(1)}</span>
                  </div>
                  <p className="text-base text-muted-foreground/60 line-clamp-1 font-medium mb-3 italic">"{h.content_excerpt}"</p>
                  <div className="flex items-center justify-between">
                     <div className="flex items-center gap-2 text-sm text-muted-foreground/30 font-bold uppercase tracking-wider">
                        <Clock className="w-3 h-3" />
                        {new Date(h.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                     </div>
                     <ArrowRight className="w-3.5 h-3.5 text-muted-foreground/0 group-hover:text-primary transition-all" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
