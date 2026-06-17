import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, Loader2 } from 'lucide-react';
import api from '../lib/api';

export default function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('user'); // 'user' or 'soc'
  const [organizationName, setOrganizationName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLogin) {
        const res = await api.post('/auth/login', { email, password });
        localStorage.setItem('sentinelx_token', res.data.access_token);
        
        // Fetch user profile to store role
        const meRes = await api.get('/auth/me');
        localStorage.setItem('sentinelx_user', JSON.stringify(meRes.data));
        
        navigate('/dashboard');
      } else {
        const payload: any = { name, email, password, role };
        if (role === 'soc') {
          payload.organization_name = organizationName;
        }
        await api.post('/auth/register', payload);
        
        // Auto login after register
        const res = await api.post('/auth/login', { email, password });
        localStorage.setItem('sentinelx_token', res.data.access_token);
        
        const meRes = await api.get('/auth/me');
        localStorage.setItem('sentinelx_user', JSON.stringify(meRes.data));
        
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred during authentication.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center py-12 sm:px-6 lg:px-8 transition-colors duration-300">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center border border-primary/20 shadow-lg">
            <ShieldAlert className="w-8 h-8 text-primary" />
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-foreground tracking-tight uppercase">
          Sentinel<span className="text-primary">X</span>
        </h2>
        <p className="mt-2 text-center text-sm text-muted-foreground font-medium">
          Secure access to the threat intelligence dashboard
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-card py-10 px-4 shadow-2xl sm:rounded-2xl sm:px-10 border border-border">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {!isLogin && (
              <>
                <div className="flex gap-4 mb-6">
                  <button
                    type="button"
                    onClick={() => setRole('user')}
                    className={`flex-1 py-2.5 rounded-xl text-sm font-bold uppercase tracking-widest border transition-all ${role === 'user' ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:bg-muted'}`}
                  >
                    Operator
                  </button>
                  <button
                    type="button"
                    onClick={() => setRole('soc')}
                    className={`flex-1 py-2.5 rounded-xl text-sm font-bold uppercase tracking-widest border transition-all ${role === 'soc' ? 'border-primary bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:bg-muted'}`}
                  >
                    SOC Admin
                  </button>
                </div>
                {role === 'soc' && (
                  <div>
                    <label className="block text-sm font-bold text-muted-foreground uppercase tracking-widest mb-1.5 ml-1">Organization</label>
                    <div className="mt-1">
                      <input
                        type="text"
                        required
                        value={organizationName}
                        onChange={(e) => setOrganizationName(e.target.value)}
                        className="appearance-none block w-full px-4 py-3 border border-border rounded-xl bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all font-semibold"
                        placeholder="e.g. Enron Finance"
                      />
                    </div>
                  </div>
                )}
                <div>
                  <label className="block text-sm font-bold text-muted-foreground uppercase tracking-widest mb-1.5 ml-1">Full Name</label>
                  <div className="mt-1">
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="appearance-none block w-full px-4 py-3 border border-border rounded-xl bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all font-semibold"
                      placeholder="e.g. John Doe"
                    />
                  </div>
                </div>
              </>
            )}
            <div>
              <label className="block text-sm font-bold text-muted-foreground uppercase tracking-widest mb-1.5 ml-1">Email address</label>
              <div className="mt-1">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="appearance-none block w-full px-4 py-3 border border-border rounded-xl bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all font-semibold"
                  placeholder="name@company.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold text-muted-foreground uppercase tracking-widest mb-1.5 ml-1">Password</label>
              <div className="mt-1">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none block w-full px-4 py-3 border border-border rounded-xl bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all font-semibold"
                  placeholder="••••••••"
                />
              </div>
            </div>

            {error && (
              <div className="text-red-500 text-sm font-bold uppercase tracking-widest bg-red-500/10 p-4 rounded-xl border border-red-500/20 italic">
                {error}
              </div>
            )}

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-4 px-4 border border-transparent rounded-xl shadow-lg text-sm font-bold uppercase tracking-widest text-white bg-primary hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary transition-all disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : (isLogin ? 'Establish Session' : 'Register Operator')}
              </button>
            </div>
          </form>

          <div className="mt-8 text-center">
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm font-bold uppercase tracking-widest text-primary hover:text-blue-500 transition-colors"
            >
              {isLogin ? "No account? Register unit" : "Existing operative? Login"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
