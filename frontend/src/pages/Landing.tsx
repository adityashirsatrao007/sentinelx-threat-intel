import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Shield, 
  Activity, 
  Lock, 
  Server, 
  ChevronRight, 
  Cpu, 
  Globe,
  Database
} from 'lucide-react';

const Landing = () => {
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden selection:bg-primary/30">
      
      {/* Navbar */}
      <nav className={`fixed top-0 w-full z-50 transition-all duration-300 border-b ${scrolled ? 'bg-background/80 backdrop-blur-md border-border py-3' : 'bg-transparent border-transparent py-5'}`}>
        <div className="max-w-7xl mx-auto px-6 lg:px-8 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-primary animate-pulse" />
            <span className="font-bold text-xl tracking-tight">SentinelX</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
            <a href="#features" className="hover:text-foreground transition-colors">Features</a>
            <a href="#platform" className="hover:text-foreground transition-colors">Platform</a>
            <a href="#security" className="hover:text-foreground transition-colors">Security</a>
            <a 
              href="https://phishing-educator.vercel.app/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-primary hover:text-primary/80 font-bold flex items-center gap-1 transition-colors relative group"
            >
              Learning
              <div className="absolute -bottom-1 left-0 w-full h-0.5 bg-primary transform scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
            </a>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => navigate('/login')}
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              Sign In
            </button>
            <button 
              onClick={() => navigate('/dashboard')}
              className="text-sm font-medium bg-foreground text-background px-4 py-2 rounded-md hover:scale-105 hover:shadow-[0_0_15px_rgba(255,255,255,0.3)] transition-all flex items-center gap-2"
            >
              Dashboard <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
        {/* Abstract Background Grid */}
        <div className="absolute inset-0 z-0 opacity-[0.03]" 
             style={{ backgroundImage: 'linear-gradient(to right, #ffffff 1px, transparent 1px), linear-gradient(to bottom, #ffffff 1px, transparent 1px)', backgroundSize: '4rem 4rem' }}>
        </div>
        
        <div className="max-w-7xl mx-auto px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold uppercase tracking-wider mb-8 shadow-[0_0_15px_rgba(var(--primary-rgb),0.15)]">
              <Activity className="w-3 h-3 animate-pulse" />
              <span>v2.0 Now Available with AI-Powered Threat Hunting</span>
            </div>
            <h1 className="text-5xl lg:text-7xl font-extrabold tracking-tight mb-6 leading-[1.1]">
              The Next Evolution in <br className="hidden md:block"/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-indigo-400 to-primary">Adaptive Cybersecurity.</span>
            </h1>
            <p className="text-lg lg:text-xl text-muted-foreground mb-10 leading-relaxed max-w-2xl mx-auto">
              SentinelX provides real-time, AI-driven monitoring and automated incident response. 
              Protect your infrastructure from sophisticated phishing, malware, and zero-day threats before they breach your perimeter.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button 
                onClick={() => navigate('/dashboard')}
                className="w-full sm:w-auto px-8 py-3.5 rounded-md bg-primary text-white font-bold hover:bg-primary/90 hover:scale-105 transition-all shadow-[0_0_25px_-5px_rgba(59,130,246,0.6)] flex items-center justify-center gap-2"
              >
                Start Monitoring <ChevronRight className="w-4 h-4" />
              </button>
              <a 
                href="https://phishing-educator.vercel.app/"
                target="_blank"
                rel="noopener noreferrer"
                className="w-full sm:w-auto px-8 py-3.5 rounded-md bg-card border border-border text-foreground font-bold hover:bg-muted hover:border-primary/50 transition-colors flex items-center justify-center gap-2 group"
              >
                <Globe className="w-4 h-4 text-primary group-hover:animate-spin-slow" /> Interactive Learning
              </a>
            </div>
            
            {/* Trust Indicators */}
            <div className="mt-16 pt-10 border-t border-border/50">
              <p className="text-sm font-semibold text-muted-foreground uppercase tracking-widest mb-6">Trusted by Forward-Thinking Security Teams</p>
              <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16 opacity-60 grayscale hover:grayscale-0 transition-all duration-500">
                <div className="flex items-center gap-2 font-bold text-xl"><Shield className="w-6 h-6" /> CyberCore</div>
                <div className="flex items-center gap-2 font-bold text-xl"><Server className="w-6 h-6" /> DataVault</div>
                <div className="flex items-center gap-2 font-bold text-xl"><Cpu className="w-6 h-6" /> QuantumSec</div>
                <div className="flex items-center gap-2 font-bold text-xl"><Lock className="w-6 h-6" /> Aegis Net</div>
              </div>
            </div>
          </div>
        </div>

        {/* Hero Visual (Mock Terminal / Interface) */}
        <div className="max-w-5xl mx-auto px-6 lg:px-8 mt-20 relative">
          <div className="rounded-xl border border-border bg-card/50 backdrop-blur-xl shadow-2xl overflow-hidden">
            {/* Window Controls */}
            <div className="h-10 border-b border-border bg-card/80 flex items-center px-4 gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
              <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
              <div className="ml-4 flex gap-2">
                <span className="text-xs text-muted-foreground font-mono">root@sentinel-core:~</span>
              </div>
            </div>
            {/* Terminal Content */}
            <div className="p-6 font-mono text-sm leading-relaxed overflow-hidden relative h-64">
              <div className="absolute inset-0 bg-gradient-to-b from-transparent to-card/50 pointer-events-none z-10" />
              <div className="text-green-500 mb-2">$ systemctl status sentinel-agent</div>
              <div className="text-foreground/80 mb-4">
                ● sentinel-agent.service - SentinelX Threat Detection Agent<br/>
                &nbsp;&nbsp;&nbsp;Loaded: loaded (/lib/systemd/system/sentinel-agent.service; enabled)<br/>
                &nbsp;&nbsp;&nbsp;Active: active (running) since Wed 2026-05-08 12:00:00 UTC<br/>
                &nbsp;Main PID: 1492 (sentinel-agent)
              </div>
              <div className="text-primary mb-2">$ tail -f /var/log/sentinel/security.log</div>
              <div className="text-muted-foreground opacity-80">
                [INFO]  Network traffic analysis initialized...<br/>
                [WARN]  Detected anomalous port scanning pattern from IP 192.168.1.45<br/>
                [ALERT] Mitigating potential DDoS attack on edge node 03...<br/>
                [INFO]  Signatures updated successfully to v2.4.1<br/>
                [INFO]  All systems optimal. Continuous monitoring active.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-card/20 border-y border-border/50">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight mb-4">Engineered for Security Teams</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Our architecture is built from the ground up to handle high-throughput log ingestion and real-time behavioral analysis.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-xl bg-card border border-border hover:border-primary/50 transition-colors group">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-6 text-primary group-hover:scale-110 transition-transform">
                <Activity className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Real-time Analytics</h3>
              <p className="text-muted-foreground leading-relaxed text-sm">
                Process millions of events per second with sub-millisecond latency. Our streaming engine instantly correlates threats across your entire stack.
              </p>
            </div>
            
            <div className="p-6 rounded-xl bg-card border border-border hover:border-primary/50 transition-colors group">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-6 text-primary group-hover:scale-110 transition-transform">
                <Shield className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Zero-Trust Architecture</h3>
              <p className="text-muted-foreground leading-relaxed text-sm">
                Built on strict zero-trust principles. Every request, regardless of origin, is authenticated, authorized, and continuously validated.
              </p>
            </div>

            <div className="p-6 rounded-xl bg-card border border-border hover:border-primary/50 transition-colors group">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-6 text-primary group-hover:scale-110 transition-transform">
                <Database className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Immutable Audit Trails</h3>
              <p className="text-muted-foreground leading-relaxed text-sm">
                Cryptographically verifiable logs ensure compliance and provide irrefutable evidence for post-incident forensic analysis.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Metrics / Social Proof */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 divide-x divide-border/50">
            <div className="text-center px-4">
              <div className="text-4xl font-extrabold text-foreground mb-2">99.99%</div>
              <div className="text-sm font-medium text-muted-foreground">Uptime SLA</div>
            </div>
            <div className="text-center px-4">
              <div className="text-4xl font-extrabold text-foreground mb-2">&lt;10ms</div>
              <div className="text-sm font-medium text-muted-foreground">Threat Detection</div>
            </div>
            <div className="text-center px-4">
              <div className="text-4xl font-extrabold text-foreground mb-2">50B+</div>
              <div className="text-sm font-medium text-muted-foreground">Events Analyzed Daily</div>
            </div>
            <div className="text-center px-4">
              <div className="text-4xl font-extrabold text-foreground mb-2">SOC 2</div>
              <div className="text-sm font-medium text-muted-foreground">Type II Certified</div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-card/30 pt-16 pb-8">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              <span className="font-semibold tracking-tight">SentinelX</span>
            </div>
            <div className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} SentinelX Systems Inc. All rights reserved.
            </div>
            <div className="flex gap-4 text-muted-foreground">
              <a href="#" className="hover:text-foreground transition-colors"><Globe className="w-5 h-5" /></a>
              <a href="#" className="hover:text-foreground transition-colors"><Server className="w-5 h-5" /></a>
              <a href="#" className="hover:text-foreground transition-colors"><Cpu className="w-5 h-5" /></a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
