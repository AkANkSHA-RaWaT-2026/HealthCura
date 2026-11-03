import api from './api';

export const getSavedSummary = async (documentId) => {
  const response = await api.get(`/summary/${documentId}`);
  return response.data;
};