import api from './apiClient.js';
export async function getDatabaseHealth() { const {data} = await api.get('/api/db/health'); return data; }
