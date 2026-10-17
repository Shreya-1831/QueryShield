import { useState } from 'react';
import { submitQuery } from '../services/queryService.js';
export default function useQuery() {
  const [loading,setLoading] = useState(false);
  const [result,setResult] = useState(null);
  const [error,setError] = useState('');
  async function run(prompt, conversationId) {
    setLoading(true); setError('');
    try { const data = await submitQuery(prompt, conversationId); setResult(data); return data; }
    catch (err) { setError(err.userMessage || err.message || 'Query failed.'); throw err; }
    finally { setLoading(false); }
  }
  return {loading,result,error,run,setResult};
}
