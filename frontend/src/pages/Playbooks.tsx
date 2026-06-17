import { Zap, Shield, Settings2, Play, Pause, Trash2 } from 'lucide-react';
import { useState } from 'react';

const PLAYBOOKS = [
  {
    id: 1,
    name: "Executive Protection Protocol",
    trigger: "Risk > 8.5 AND Target == 'Executive'",
    actions: ["Lock Corporate Account", "Quarantine Email", "Notify CISO"],
    status: "Active",
    executions: 4
  },
  {
    id: 2,
    name: "Finance Fraud Prevention",
    trigger: "Behavior == 'financial_coercion' AND Risk > 7.0",
    actions: ["Hold Outbound Wire Transfers", "Force MFA Re-auth"],
    status: "Active",
    executions: 12
  },
  {
    id: 3,
    name: "Vishing Deepfake Mitigation",
    trigger: "AI Voice Prob > 80%",
    actions: ["Terminate Call Session", "Log Forensic Audio"],
    status: "Paused",
    executions: 2
  },
  {
    id: 4,
    name: "Internal Phish Hunting",
    trigger: "Sender Domain == 'enron-internal.com' AND Risk > 6.0",
    actions: ["Flag in Slack #soc-alerts", "Request Peer Review"],
    status: "Active",
    executions: 89
  }
];

export default function Playbooks() {
  const [playbooks, setPlaybooks] = useState(PLAYBOOKS);
  const [executing, setExecuting] = useState<number | null>(null);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState('');

  const runPlaybook = async (id: number, actions: string[]) => {
    if (executing !== null) return;
    setExecuting(id);
    setCurrentStep(0);
    setProgress(0);

    for (let i = 0; i < actions.length; i++) {
      setCurrentStep(i);
      const subSteps = ["Initializing", "Verifying Protocol", "Applying Rule", "Syncing SOC"];
      for (let s = 0; s < subSteps.length; s++) {
        setStatusMsg(`${actions[i]} — ${subSteps[s]}`);
        for (let p = (s * 25); p <= ((s + 1) * 25); p += 5) {
          setProgress(p);
          await new Promise(resolve => setTimeout(resolve, 40));
        }
      }
    }
    
    setCurrentStep(actions.length);
    // Increment execution count
    setPlaybooks(prev => prev.map(p => p.id === id ? { ...p, executions: p.executions + 1 } : p));
    
    await new Promise(resolve => setTimeout(resolve, 1000));
    setExecuting(null);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto animate-fade-in transition-colors duration-300">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-8 mb-12">
        <div>
          <div className="flex items-center gap-2.5 text-primary mb-2.5">
            <Zap className="w-4 h-4 fill-current" />
            <span className="text-sm font-bold uppercase tracking-[0.3em]">Automatic Actions</span>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight leading-none uppercase">
            Automated <span className="text-muted-foreground/30">Responses</span>
          </h1>
          <p className="text-muted-foreground mt-4 max-w-lg font-medium leading-relaxed">
            Configure automated security actions. The system will automatically run these sequences when suspicious activity is detected.
          </p>
        </div>
        
        <button className="bg-primary hover:bg-blue-600 text-white px-8 py-4 rounded-2xl font-bold uppercase tracking-widest text-sm shadow-lg shadow-primary/20 transition-all flex items-center gap-3">
          <Settings2 className="w-4 h-4" />
          New Automation
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {playbooks.map((p) => (
          <div key={p.id} className="bg-card border border-border rounded-3xl p-8 relative overflow-hidden group shadow-sm transition-all hover:border-primary/20">
            <div className={`absolute top-0 right-0 p-8 opacity-[0.03] transition-transform group-hover:scale-110`}>
              <Shield className="w-32 h-32 text-foreground" />
            </div>
            
            <div className="flex items-start justify-between mb-8 relative z-10">
              <div>
                <h3 className="text-xl font-bold text-foreground tracking-tight mb-2 uppercase italic">{p.name}</h3>
                <div className="flex items-center gap-2">
                   <div className={`w-1.5 h-1.5 rounded-full ${p.status === 'Active' ? 'bg-emerald-500 animate-pulse' : 'bg-muted-foreground/30'}`} />
                   <span className={`text-sm font-bold uppercase tracking-widest ${p.status === 'Active' ? 'text-emerald-500' : 'text-muted-foreground/30'}`}>{p.status}</span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-foreground leading-none font-mono">{p.executions}</p>
                <p className="text-sm font-bold uppercase tracking-widest text-muted-foreground/40 mt-1">Executions</p>
              </div>
            </div>

            <div className="space-y-6 relative z-10">
              <div className="bg-background border border-border p-4 rounded-xl shadow-inner">
                <p className="text-sm font-bold uppercase text-muted-foreground tracking-widest mb-2">When this runs</p>
                <p className="text-sm font-mono text-primary font-bold">{p.trigger}</p>
              </div>

              <div>
                <p className="text-sm font-bold uppercase text-muted-foreground tracking-widest mb-3">Actions to take</p>
                <div className="flex flex-wrap gap-2">
                  {p.actions.map((a, i) => (
                    <span 
                      key={i} 
                      className={`px-3 py-1.5 rounded-xl border text-sm font-bold transition-colors ${
                        executing === p.id && currentStep === i
                          ? 'bg-primary text-white border-primary'
                          : executing === p.id && currentStep > i
                          ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
                          : 'bg-muted border-border text-muted-foreground'
                      }`}
                    >
                      {a}
                    </span>
                  ))}
                </div>
              </div>

              {/* Interactive Execution Area */}
              <div className="pt-6 border-t border-border relative z-10">
                {executing === p.id ? (
                  <div className="bg-primary/5 border border-primary/20 rounded-2xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-sm font-bold text-primary uppercase tracking-widest animate-pulse">
                        {currentStep < p.actions.length ? statusMsg : 'Protocol Complete'}
                      </span>
                      <span className="text-sm font-bold text-primary font-mono">
                        {currentStep < p.actions.length ? `${progress}%` : '100%'}
                      </span>
                    </div>
                    <div className="w-full bg-muted h-2 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary transition-all ease-linear"
                        style={{ width: currentStep < p.actions.length ? `${progress}%` : '100%' }}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="flex gap-3">
                    <button 
                      onClick={() => runPlaybook(p.id, p.actions)}
                      disabled={executing !== null}
                      className="flex-1 py-3 rounded-xl bg-background border border-border hover:bg-muted text-foreground text-sm font-bold uppercase tracking-widest transition-all flex items-center justify-center gap-2 shadow-sm disabled:opacity-50"
                    >
                      <Play className="w-4 h-4 text-primary" />
                      Manually Execute
                    </button>
                    <button className="flex-1 py-3 rounded-xl bg-background border border-border hover:bg-muted text-foreground text-sm font-bold uppercase tracking-widest transition-all flex items-center justify-center gap-2 shadow-sm">
                      {p.status === 'Active' ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3 text-muted-foreground" />}
                      {p.status === 'Active' ? 'Pause' : 'Resume'}
                    </button>
                    <button className="p-3 rounded-xl bg-background border border-border hover:bg-red-500/10 text-muted-foreground hover:text-red-500 transition-all shadow-sm">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {/* Placeholder for new playbook */}
        <div className="border-2 border-dashed border-border rounded-3xl flex flex-col items-center justify-center p-12 hover:border-primary/40 transition-all group cursor-pointer bg-muted/20">
           <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4 group-hover:bg-primary/10 transition-all">
              <Zap className="w-6 h-6 text-muted-foreground group-hover:text-primary" />
           </div>
           <p className="text-sm font-bold uppercase tracking-widest text-muted-foreground group-hover:text-foreground">Add New Automation</p>
        </div>
      </div>
    </div>
  );
}
