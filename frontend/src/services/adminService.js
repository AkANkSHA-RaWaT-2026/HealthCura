import api from './api';

export const getAdminStats = async () => {
  const response = await api.get('/admin/stats');
  return response.data;
};

export const getPatients = async () => {
  const response = await api.get('/admin/patients');
  return response.data;
};

export const exportPatientReport = async (patientId) => {
  const response = await api.post(`/admin/export/${patientId}`, null, {
    responseType: 'blob',
  });
  return response.data;
};