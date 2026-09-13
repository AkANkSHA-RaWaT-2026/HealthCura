import api from './api';

export const askQuestion = async (question) => {
  const response = await api.post('/chat/ask', { question });
  return response.data;
};

export const getChatHistory = async () => {
  const response = await api.get('/chat/history');
  return response.data;
};