import { createContext, useCallback, useEffect, useMemo, useState } from 'react';
import { getIdentity } from '../services/authService.js';
export const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState('checking');
  const [error, setError] = useState('');
  const refreshIdentity = useCallback(async () => {
    setStatus('checking'); setError('');
    try {
      const data = await getIdentity();
      if (data?.authenticated === false) { setUser(null); setStatus('anonymous'); return null; }
      const identity = data?.user ?? data?.identity ?? data;
      setUser(identity); setStatus('authenticated'); return identity;
    } catch (err) {
      setUser(null);
      setStatus(err?.response?.status === 401 ? 'anonymous' : 'unavailable');
      setError(err?.response?.status === 401 ? 'Windows identity has not been verified by the backend.' : 'Could not reach the local QueryShield API.');
      return null;
    }
  }, []);
  useEffect(() => { refreshIdentity(); }, [refreshIdentity]);
  const value = useMemo(() => ({user, status, error, refreshIdentity, setUser}), [user,status,error,refreshIdentity]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
