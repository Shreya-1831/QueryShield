
import axios from 'axios';

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '');

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 330000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
      error.userMessage =
        'The local AI query timed out. Check whether Ollama is responding and try again.';
    } else if (!error.response) {
      error.userMessage =
        `Cannot reach QueryShield API at ${API_BASE_URL}. Check that FastAPI is running.`;
    } else {
      error.userMessage =
        error.response.data?.detail ||
        error.response.data?.message ||
        `Request failed (${error.response.status}).`;
    }

    return Promise.reject(error);
  }
);

export default apiClient;
