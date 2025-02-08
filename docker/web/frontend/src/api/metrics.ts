import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
});

export interface Metrics {
  builds: {
    total_builds: number;
    successful_builds: number;
    failed_builds: number;
    average_duration: number;
    build_frequency: number;
  };
  pipelines: {
    total_runs: number;
    successful_runs: number;
    failed_runs: number;
    average_duration: number;
  };
  recommendations: string[];
}

export const fetchMetrics = async (): Promise<Metrics> => {
  const response = await api.get<Metrics>('/metrics');
  return response.data;
};