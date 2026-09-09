import api from './api';

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getMyDocuments = async () => {
  const response = await api.get('/documents/');
  return response.data;
};

export const getDocument = async (documentId) => {
  const response = await api.get(`/documents/${documentId}`);
  return response.data;
};

export const generateSummary = async (documentId) => {
  const response = await api.post(`/summary/generate/${documentId}`);
  return response.data;
};

export const deleteDocument = async (documentId) => {
  await api.delete(`/documents/${documentId}`);
};