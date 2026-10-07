import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/auth';
import { Network, Eye, EyeOff, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 800));

    const success = login(username, password);
    if (success) {
      navigate('/');
    } else {
      setError('Invalid credentials. Please try again.');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-noc-bg relative overflow-hidden">
      {/* Background pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, rgba(14, 165, 233, 0.3) 1px, transparent 0)`,
          backgroundSize: '40px 40px'
        }} />
      </div>

      {/* Gradient orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-noc-primary/5 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-noc-info/5 rounded-full blur-3xl" />

      <div className="relative z-10 w-full max-w-md px-6">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-noc-primary/10 border border-noc-primary/20 mb-4">
            <Network className="w-8 h-8 text-noc-primary" />
          </div>
          <h1 className="text-2xl font-bold text-noc-text">PNMP</h1>
          <p className="text-sm text-noc-text-muted mt-1">PSSN Network Management Platform</p>
        </div>

        {/* Login form */}
        <div className="bg-noc-surface border border-noc-border rounded-xl p-6 shadow-xl">
          <h2 className="text-lg font-semibold text-noc-text mb-1">Sign In</h2>
          <p className="text-sm text-noc-text-muted mb-6">Enter your credentials to access the platform</p>

          {error && (
            <div className="flex items-center gap-2 p-3 mb-4 bg-noc-danger/10 border border-noc-danger/20 rounded-lg">
              <AlertCircle className="w-4 h-4 text-noc-danger flex-shrink-0" />
              <span className="text-sm text-noc-danger">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3 py-2.5 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text placeholder-noc-text-muted/50 focus:outline-none focus:border-noc-primary focus:ring-1 focus:ring-noc-primary/50 transition-all"
                placeholder="Enter username"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-noc-text-muted mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2.5 bg-noc-bg border border-noc-border rounded-lg text-sm text-noc-text placeholder-noc-text-muted/50 focus:outline-none focus:border-noc-primary focus:ring-1 focus:ring-noc-primary/50 transition-all pr-10"
                  placeholder="Enter password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-noc-text-muted hover:text-noc-text"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-noc-primary hover:bg-noc-primary/90 text-white font-medium text-sm rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="mt-4 pt-4 border-t border-noc-border">
            <p className="text-xs text-noc-text-muted text-center">
              Demo: Use <span className="text-noc-primary font-mono">admin</span> / <span className="text-noc-primary font-mono">admin</span>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-xs text-noc-text-muted">
            PNMP v1.0.0 • PSSN Network Management Platform
          </p>
        </div>
      </div>
    </div>
  );
}
