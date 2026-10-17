import { createContext, useCallback, useMemo, useState } from 'react';
import { X, CheckCircle2, AlertCircle, Info } from 'lucide-react';
export const NotificationContext = createContext(null);
export function NotificationProvider({ children }) {
  const [items, setItems] = useState([]);
  const notify = useCallback((message, type='info') => {
    const id = `${Date.now()}-${Math.random()}`;
    setItems(prev => [...prev, {id, message, type}]);
    window.setTimeout(() => setItems(prev => prev.filter(x => x.id !== id)), 4200);
  }, []);
  const value = useMemo(() => ({notify}), [notify]);
  const Icon = ({type}) => type === 'success' ? <CheckCircle2 size={17}/> : type === 'error' ? <AlertCircle size={17}/> : <Info size={17}/>;
  return <NotificationContext.Provider value={value}>
    {children}
    <div className="toast-stack" aria-live="polite">{items.map(item => <div className={`toast toast-${item.type}`} key={item.id}><Icon type={item.type}/><span>{item.message}</span><button className="icon-button" aria-label="Dismiss" onClick={() => setItems(p => p.filter(x => x.id !== item.id))}><X size={15}/></button></div>)}</div>
  </NotificationContext.Provider>;
}
