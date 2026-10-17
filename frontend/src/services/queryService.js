import api from './apiClient.js';
export async function submitQuery(prompt, conversationId) {
  const payload = {prompt};
  if (conversationId) payload.conversation_id = conversationId;
  const {data} = await api.post('/api/query', payload);
  return data;
}
