import api from './apiClient.js';
export async function getIdentity() { const {data} = await api.get('/api/auth/me'); return data; }
export async function checkDatabaseAccess(employeeId) { const {data} = await api.get(`/api/auth/database/${encodeURIComponent(employeeId)}`); return data; }
