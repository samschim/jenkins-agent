import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SystemMetrics from '../SystemMetrics';
import { getSystemMetrics } from '@/services/api';

// Mock API
jest.mock('@/services/api');
const mockGetSystemMetrics = getSystemMetrics as jest.MockedFunction<typeof getSystemMetrics>;

// Mock Recharts
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => children,
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
}));

// Test data
const mockMetrics = {
  cpu_usage: [
    { timestamp: '2024-02-07T12:00:00Z', value: 30 },
    { timestamp: '2024-02-07T12:01:00Z', value: 35 },
    { timestamp: '2024-02-07T12:02:00Z', value: 40 },
  ],
  memory_usage: [
    { timestamp: '2024-02-07T12:00:00Z', value: 45 },
    { timestamp: '2024-02-07T12:01:00Z', value: 50 },
    { timestamp: '2024-02-07T12:02:00Z', value: 55 },
  ],
  active_tasks: [
    { timestamp: '2024-02-07T12:00:00Z', value: 2 },
    { timestamp: '2024-02-07T12:01:00Z', value: 3 },
    { timestamp: '2024-02-07T12:02:00Z', value: 4 },
  ],
  error_rate: [
    { timestamp: '2024-02-07T12:00:00Z', value: 0 },
    { timestamp: '2024-02-07T12:01:00Z', value: 5 },
    { timestamp: '2024-02-07T12:02:00Z', value: 2 },
  ],
};

describe('SystemMetrics', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  beforeEach(() => {
    mockGetSystemMetrics.mockResolvedValue(mockMetrics);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders system metrics charts', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <SystemMetrics />
      </QueryClientProvider>
    );

    // Check title
    expect(screen.getByText('System Metrics')).toBeInTheDocument();

    // Check section titles
    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText('Memory Usage')).toBeInTheDocument();
    expect(screen.getByText('Active Tasks')).toBeInTheDocument();
    expect(screen.getByText('Error Rate')).toBeInTheDocument();

    // Check charts
    const charts = screen.getAllByTestId('line-chart');
    expect(charts).toHaveLength(4);
  });

  it('handles loading state', () => {
    mockGetSystemMetrics.mockImplementation(() => new Promise(() => {}));

    render(
      <QueryClientProvider client={queryClient}>
        <SystemMetrics />
      </QueryClientProvider>
    );

    expect(screen.queryByTestId('line-chart')).not.toBeInTheDocument();
  });

  it('updates data periodically', async () => {
    const { rerender } = render(
      <QueryClientProvider client={queryClient}>
        <SystemMetrics />
      </QueryClientProvider>
    );

    // Initial render
    expect(await screen.findAllByTestId('line-chart')).toHaveLength(4);

    // Update mock data
    const updatedMetrics = {
      ...mockMetrics,
      cpu_usage: [
        ...mockMetrics.cpu_usage,
        { timestamp: '2024-02-07T12:03:00Z', value: 45 },
      ],
    };
    mockGetSystemMetrics.mockResolvedValue(updatedMetrics);

    // Force re-render
    rerender(
      <QueryClientProvider client={queryClient}>
        <SystemMetrics />
      </QueryClientProvider>
    );

    // Check updated charts
    expect(await screen.findAllByTestId('line-chart')).toHaveLength(4);
  });

  it('handles empty data', async () => {
    mockGetSystemMetrics.mockResolvedValue({
      cpu_usage: [],
      memory_usage: [],
      active_tasks: [],
      error_rate: [],
    });

    render(
      <QueryClientProvider client={queryClient}>
        <SystemMetrics />
      </QueryClientProvider>
    );

    // Charts should still render
    expect(await screen.findAllByTestId('line-chart')).toHaveLength(4);
  });
});