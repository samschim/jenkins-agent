import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface TaskRequest {
  task: string;
  agent_type?: string;
}

export interface TaskResponse {
  status: string;
  result: any;
  task: string;
  agent_type: string;
}

export const executeTask = async (request: TaskRequest): Promise<TaskResponse> => {
  const response = await api.post<TaskResponse>('/task', request);
  return response.data;
};

export const listAgents = async () => {
  const response = await api.get('/agents');
  return response.data;
};

export const login = async (username: string, password: string) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);

  const response = await api.post('/token', formData);
  const { access_token } = response.data;
  localStorage.setItem('token', access_token);
  return access_token;
};

export const logout = () => {
  localStorage.removeItem('token');
};

// WebSocket connection
export const createWebSocket = () => {
  const token = localStorage.getItem('token');
  if (!token) return null;

  const ws = new WebSocket(`ws://${API_URL.replace('http://', '')}/ws`);
  
  ws.onopen = () => {
    console.log('WebSocket connected');
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  return ws;
};

export default api;