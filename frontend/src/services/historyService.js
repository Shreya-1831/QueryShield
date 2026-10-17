
import api from './apiClient.js';

export async function getQueryHistory() {
  const { data } = await api.get('/api/query/history');

  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(data?.history)) return data.history;

  return [];
}
