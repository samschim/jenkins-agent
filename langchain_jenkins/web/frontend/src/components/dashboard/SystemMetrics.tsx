import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Grid,
  Typography,
  Box,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { getSystemMetrics } from '@/services/api';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { format } from 'date-fns';

interface MetricPoint {
  timestamp: string;
  value: number;
}

interface SystemMetrics {
  cpu_usage: MetricPoint[];
  memory_usage: MetricPoint[];
  active_tasks: MetricPoint[];
  error_rate: MetricPoint[];
}

const SystemMetrics: React.FC = () => {
  const { data: metrics, isLoading } = useQuery<SystemMetrics>({
    queryKey: ['metrics'],
    queryFn: getSystemMetrics,
    refetchInterval: 10000,
  });

  if (isLoading || !metrics) {
    return null;
  }

  const formatTime = (timestamp: string) => {
    return format(new Date(timestamp), 'HH:mm:ss');
  };

  return (
    <Card>
      <CardHeader title="System Metrics" />
      <CardContent>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              CPU Usage
            </Typography>
            <Box sx={{ height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics.cpu_usage}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={formatTime}
                    interval="preserveStartEnd"
                  />
                  <YAxis unit="%" domain={[0, 100]} />
                  <Tooltip
                    labelFormatter={formatTime}
                    formatter={(value: number) => [`${value}%`, 'CPU Usage']}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#8884d8"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              Memory Usage
            </Typography>
            <Box sx={{ height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics.memory_usage}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={formatTime}
                    interval="preserveStartEnd"
                  />
                  <YAxis unit="%" domain={[0, 100]} />
                  <Tooltip
                    labelFormatter={formatTime}
                    formatter={(value: number) => [`${value}%`, 'Memory Usage']}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#82ca9d"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              Active Tasks
            </Typography>
            <Box sx={{ height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics.active_tasks}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={formatTime}
                    interval="preserveStartEnd"
                  />
                  <YAxis domain={[0, 'auto']} />
                  <Tooltip
                    labelFormatter={formatTime}
                    formatter={(value: number) => [value, 'Active Tasks']}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#ffc658"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              Error Rate
            </Typography>
            <Box sx={{ height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics.error_rate}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={formatTime}
                    interval="preserveStartEnd"
                  />
                  <YAxis unit="%" domain={[0, 100]} />
                  <Tooltip
                    labelFormatter={formatTime}
                    formatter={(value: number) => [`${value}%`, 'Error Rate']}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#ff7300"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default SystemMetrics;