import api from './apiClient.js';
export async function getApiHealth() { const {data} = await api.get('/health'); return data; }
export async function getDatabaseHealth() { const {data} = await api.get('/api/db/health'); return data; }
