import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';

export default function AuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const token = searchParams.get('sentinelx_token');
    const userParam = searchParams.get('sentinelx_user');
    if (token) {
      localStorage.setItem('sentinelx_token', token);
      if (userParam) {
        try {
          localStorage.setItem('sentinelx_user', userParam);
        } catch {
          // ignore
        }
      }
      navigate('/dashboard', { replace: true });
    } else {
      navigate('/login', { replace: true });
    }
  }, [navigate, searchParams]);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center">
      <ShieldAlert className="w-12 h-12 text-primary animate-pulse" />
      <p className="mt-4 text-muted-foreground text-sm font-medium">Completing authentication...</p>
    </div>
  );
}
