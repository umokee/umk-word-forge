import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { setApiKey, apiFetch } from './api/client';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30000, retry: 1 },
  },
});

function AuthGate({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<'checking' | 'ok' | 'need_key' | 'error'>('checking');
  const [key, setKey] = useState('');
  const [error, setError] = useState('');
  const [connectError, setConnectError] = useState('');

  const checkAuth = () => {
    setState('checking');
    setConnectError('');
    apiFetch('/auth/check')
      .then(() => setState('ok'))
      .catch((e: Error) => {
        if (e.message === 'AUTH_REQUIRED') {
          setState('need_key');
        } else if (/^HTTP 50[234]$/.test(e.message)) {
          // Gateway error — backend is unreachable behind the reverse proxy
          setConnectError(e.message);
          setState('error');
        } else if (e.message.startsWith('HTTP ')) {
          // Other HTTP status — server is up, try open access
          setState('ok');
        } else {
          // Network error or backend unreachable
          setConnectError(e.message || 'Cannot reach backend');
          setState('error');
        }
      });
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const submit = () => {
    setApiKey(key);
    setError('');
    apiFetch('/auth/check')
      .then(() => {
        setState('ok');
        queryClient.invalidateQueries();
      })
      .catch((e: Error) => {
        if (e.message === 'AUTH_REQUIRED') setError('Invalid API key');
        else setError(e.message || 'Connection error');
      });
  };

  if (state === 'checking') {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0A0A0B]">
        <div className="animate-pulse text-[#5C5C66] text-sm">Connecting...</div>
      </div>
    );
  }

  if (state === 'error') {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0A0A0B]">
        <div className="bg-[#141416] border border-[#2A2A30] rounded-sm p-8 w-full max-w-sm text-center">
          <h1 className="text-xl font-bold text-[#E8E8EC] mb-1">WordForge</h1>
          <p className="text-sm text-red-400 mb-4">{connectError || 'Cannot connect to server'}</p>
          <p className="text-xs text-[#5C5C66] mb-6">The backend service may be starting up. Please wait and try again.</p>
          <button
            onClick={checkAuth}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white rounded-sm px-4 py-2 text-sm transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (state === 'need_key') {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0A0A0B]">
        <div className="bg-[#141416] border border-[#2A2A30] rounded-sm p-8 w-full max-w-sm">
          <h1 className="text-xl font-bold text-[#E8E8EC] mb-1">WordForge</h1>
          <p className="text-sm text-[#5C5C66] mb-6">Enter your API key to continue</p>
          <input
            type="password"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && submit()}
            placeholder="API Key"
            className="w-full bg-[#1C1C20] border border-[#2A2A30] focus:border-indigo-500 text-[#E8E8EC] rounded-sm px-3 py-2 text-sm outline-none mb-3"
            autoFocus
          />
          {error && <p className="text-red-400 text-xs mb-3">{error}</p>}
          <button
            onClick={submit}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white rounded-sm px-4 py-2 text-sm transition-colors"
          >
            Unlock
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthGate>
          <App />
        </AuthGate>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
