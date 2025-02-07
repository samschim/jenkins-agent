import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getAgentStatus = async () => {
  const response = await api.get('/agents/status');
  return response.data;
};

export const getTaskHistory = async () => {
  const response = await api.get('/tasks/history');
  return response.data;
};

export const getSystemMetrics = async () => {
  const response = await api.get('/system/metrics');
  return response.data;
};

export const getErrorAnalysis = async () => {
  const response = await api.get('/errors/analysis');
  return response.data;
};

export const startTask = async (description: string, agent?: string) => {
  const response = await api.post('/tasks', { description, agent });
  return response.data;
};

export const stopTask = async (taskId: string) => {
  const response = await api.post(`/tasks/${taskId}/stop`);
  return response.data;
};

export const getTaskDetails = async (taskId: string) => {
  const response = await api.get(`/tasks/${taskId}`);
  return response.data;
};

export const getAgentLogs = async (agentId: string) => {
  const response = await api.get(`/agents/${agentId}/logs`);
  return response.data;
};

export const updateAgentConfig = async (agentId: string, config: any) => {
  const response = await api.put(`/agents/${agentId}/config`, config);
  return response.data;
};

export const getSystemHealth = async () => {
  const response = await api.get('/system/health');
  return response.data;
};

export const getErrorTrends = async () => {
  const response = await api.get('/errors/trends');
  return response.data;
};

export const getErrorSolutions = async (errorType: string) => {
  const response = await api.get(`/errors/${errorType}/solutions`);
  return response.data;
};

export const getAgentMetrics = async (agentId: string) => {
  const response = await api.get(`/agents/${agentId}/metrics`);
  return response.data;
};

export const getTaskMetrics = async () => {
  const response = await api.get('/tasks/metrics');
  return response.data;
};

export const getErrorMetrics = async () => {
  const response = await api.get('/errors/metrics');
  return response.data;
};

// Error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server error
      console.error('Server Error:', error.response.data);
    } else if (error.request) {
      // Network error
      console.error('Network Error:', error.request);
    } else {
      // Other error
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);