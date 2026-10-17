import { useCallback, useEffect, useState } from 'react';
import { getApiHealth, getDatabaseHealth } from '../services/healthService.js';
export default function useHealth() {
  const [health, setHealth] = useState({loading:true, api:null, database:null, error:''});
  const refresh = useCallback(async () => {
    setHealth(s => ({...s, loading:true, error:''}));
    const [api, database] = await Promise.allSettled([getApiHealth(), getDatabaseHealth()]);
    setHealth({loading:false, api:api.status==='fulfilled'?api.value:null, database:database.status==='fulfilled'?database.value:null,
      error:api.status==='rejected' ? api.reason.userMessage || api.reason.message : database.status==='rejected' ? database.reason.userMessage || database.reason.message : ''});
  }, []);
  useEffect(() => { refresh(); }, [refresh]);
  return {...health, refresh};
}
