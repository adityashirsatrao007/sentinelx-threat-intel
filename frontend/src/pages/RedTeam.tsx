import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Target, Crosshair, AlertTriangle, ShieldAlert, Cpu, Loader2, Copy, CheckCircle2, ArrowRight, Search, Smartphone } from 'lucide-react';
import api from '../lib/api';

export default function RedTeam() {
  const navigate = useNavigate();
  const [severity, setSeverity] = useState(50);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [copied, setCopied] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedBody, setStreamedBody] = useState('');

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setStreamedBody('');

    try {
      const response = await api.get(`/analyze/dataset-samples?percentile=${severity / 100}`);
      const payload = response.data;
      setResult(payload);
      
      // Typewriter streaming effect
      setIsStreaming(true);
      let currentText = "";
      // Cap streaming to 500 characters so it doesn't take forever on long emails
      const bodyToStream = payload.body.substring(0, 500) + (payload.body.length > 500 ? "..." : "");
      
      for (let i = 0; i < bodyToStream.length; i++) {
        currentText += bodyToStream[i];
        setStreamedBody(currentText);
        await new Promise(resolve => setTimeout(resolve, 5)); // fast typing speed
      }
      setIsStreaming(false);
    } catch (err) {
      console.error(err);
      alert("Failed to fetch dataset sample. Ensure the backend script was run.");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = () => {
    if (result) {
      navigate('/analyze', { 
        state: { 
          sender: result.sender, 
          subject: result.subject, 
          body: result.body,
          type: 'email' 
        } 
      });
    }
  };

  const handleSendToMobile = async () => {
    if (result) {
      setLoading(true);
      try {
        await api.post('/analyze/email', { 
          sender: result.sender, 
          body: result.body,
          subject: result.subject,
          force_risk_score: result.risk_score || 9.8 // Use precalculated dataset score
        });
        alert("Attack payload successfully launched to mobile dashboard!");
      } catch (err) {
        console.error(err);
        alert("Failed to send attack payload to mobile device.");
      } finally {
        setLoading(false);
      }
    }
  };

  const handleCopy = () => {
    if (result) {
      navigator.clipboard.writeText(`Sender: ${result.sender}\nSubject: ${result.subject}\n\n${result.body}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto animate-fade-in transition-colors duration-300">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-8 mb-12">
        <div>
          <div className="flex items-center gap-2.5 text-red-500 mb-2.5">
            <Crosshair className="w-5 h-5 animate-pulse" />
            <span className="text-sm font-bold uppercase tracking-[0.3em]">Offensive AI Engine</span>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight leading-none uppercase">
            Red Team <span className="text-muted-foreground/30">Generator</span>
          </h1>
          <p className="text-muted-foreground mt-4 max-w-lg font-medium leading-relaxed">
            Generate sophisticated, context-aware phishing payloads to test your organization's resilience. Ensure your employees are prepared for AI-driven social engineering attacks.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Configuration Panel */}
        <div className="bg-card border border-border rounded-3xl p-8 relative overflow-hidden group shadow-sm">
          <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
            <Target className="w-32 h-32" />
          </div>
          <form onSubmit={handleGenerate} className="space-y-8 relative z-10">
            <div>
              <div className="flex justify-between items-center mb-3">
                <label className="block text-sm font-bold uppercase text-muted-foreground tracking-widest">Threat Severity</label>
                <span className={`font-bold ${severity > 80 ? 'text-red-500' : severity > 40 ? 'text-orange-500' : 'text-green-500'}`}>
                  {severity > 80 ? 'CRITICAL (Malicious)' : severity > 40 ? 'MEDIUM (Suspicious)' : 'LOW (Safe)'}
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={severity}
                onChange={(e) => setSeverity(Number(e.target.value))}
                className="w-full h-3 bg-muted rounded-lg appearance-none cursor-pointer accent-red-500"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-2 font-semibold uppercase tracking-widest">
                <span>Safe (Enron Ham)</span>
                <span>Critical (Phishing)</span>
              </div>
            </div>

            <div className="pt-4 border-t border-border">
              <button
                type="submit"
                disabled={loading || isStreaming}
                className="w-full py-5 px-6 bg-red-500 hover:bg-red-600 disabled:bg-muted disabled:text-muted-foreground rounded-2xl font-bold uppercase tracking-[0.2em] text-white shadow-lg shadow-red-500/20 transition-all flex items-center justify-center gap-3 group/btn"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : (
                  <>
                    <Cpu className="w-5 h-5" />
                    Fetch Dataset Sample
                    <ArrowRight className="w-5 h-5 group-hover/btn:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Output Panel */}
        <div className="bg-card border border-border rounded-3xl p-8 shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-orange-500" /> Output Payload
            </h3>
            {result && (
              <div className="flex gap-4">
                <button
                  onClick={handleAnalyze}
                  className="flex items-center gap-2 text-sm font-bold uppercase tracking-widest text-primary hover:text-foreground transition-colors"
                >
                  <Search className="w-4 h-4" />
                  Analyze
                </button>
                <button
                  onClick={handleSendToMobile}
                  className="flex items-center gap-2 text-sm font-bold uppercase tracking-widest text-orange-500 hover:text-orange-400 transition-colors"
                >
                  <Smartphone className="w-4 h-4" />
                  Send to Mobile
                </button>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-2 text-sm font-bold uppercase tracking-widest text-primary hover:text-foreground transition-colors"
                >
                  {copied ? <CheckCircle2 className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
            )}
          </div>

          <div className="flex-1 bg-background border border-border rounded-2xl p-6 shadow-inner relative">
            {loading ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground/50">
                <Loader2 className="w-10 h-10 animate-spin mb-4 text-red-500/50" />
                <p className="text-sm font-bold uppercase tracking-widest animate-pulse">Generating LLM Payload...</p>
              </div>
            ) : result ? (
              <div className="space-y-5 animate-fade-in text-foreground">
                <div className="flex items-start gap-4 pb-5 border-b border-border">
                  <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-500 shrink-0">
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-1">Spoofed Sender</p>
                    <p className="font-semibold">{result.sender}</p>
                  </div>
                </div>
                
                <div>
                  <p className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-2">Subject Header</p>
                  <p className="font-bold text-lg">{result.subject}</p>
                </div>
                
                <div>
                  <p className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-2">Message Body</p>
                  <p className="leading-relaxed font-medium">
                    {streamedBody}
                    {isStreaming && <span className="inline-block w-2 h-4 bg-red-500 ml-1 animate-pulse" />}
                  </p>
                </div>
              </div>
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground/20">
                <Crosshair className="w-16 h-16 mb-4" />
                <p className="text-sm font-bold uppercase tracking-widest">Awaiting Generation</p>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
