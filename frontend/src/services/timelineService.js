// frontend/src/services/timelineService.js
import api from './api';

export const getMyTimeline = async () => {
  const response = await api.get('/timeline/');
  return response.data;
};