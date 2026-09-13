import api from './api';

export const downloadDischargeSummary = async () => {
  const response = await api.post('/discharge/generate', null, {
    responseType: 'blob',
  });
  return response.data;
};