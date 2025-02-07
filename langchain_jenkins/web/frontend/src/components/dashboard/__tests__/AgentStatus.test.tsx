import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AgentStatus from '../AgentStatus';
import { getAgentStatus } from '@/services/api';

// Mock API
jest.mock('@/services/api');
const mockGetAgentStatus = getAgentStatus as jest.MockedFunction<typeof getAgentStatus>;

// Test data
const mockAgents = [
  {
    name: 'build-manager',
    status: 'online',
    tasks: 2,
    memory_usage: 45,
    cpu_usage: 30,
  },
  {
    name: 'log-analyzer',
    status: 'busy',
    tasks: 1,
    memory_usage: 60,
    cpu_usage: 80,
  },
];

describe('AgentStatus', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  beforeEach(() => {
    mockGetAgentStatus.mockResolvedValue(mockAgents);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders agent status cards', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <AgentStatus />
      </QueryClientProvider>
    );

    // Check title
    expect(screen.getByText('Agent Status')).toBeInTheDocument();

    // Wait for data to load
    expect(await screen.findByText('build-manager')).toBeInTheDocument();
    expect(screen.getByText('log-analyzer')).toBeInTheDocument();

    // Check status chips
    expect(screen.getByText('online')).toBeInTheDocument();
    expect(screen.getByText('busy')).toBeInTheDocument();

    // Check task counts
    expect(screen.getByText('2 active tasks')).toBeInTheDocument();
    expect(screen.getByText('1 active tasks')).toBeInTheDocument();

    // Check resource usage
    expect(screen.getByText('CPU: 30%')).toBeInTheDocument();
    expect(screen.getByText('Memory: 45%')).toBeInTheDocument();
    expect(screen.getByText('CPU: 80%')).toBeInTheDocument();
    expect(screen.getByText('Memory: 60%')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    mockGetAgentStatus.mockImplementation(() => new Promise(() => {}));

    render(
      <QueryClientProvider client={queryClient}>
        <AgentStatus />
      </QueryClientProvider>
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles empty data', async () => {
    mockGetAgentStatus.mockResolvedValue([]);

    render(
      <QueryClientProvider client={queryClient}>
        <AgentStatus />
      </QueryClientProvider>
    );

    expect(await screen.findByText('Agent Status')).toBeInTheDocument();
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });

  it('updates data periodically', async () => {
    const { rerender } = render(
      <QueryClientProvider client={queryClient}>
        <AgentStatus />
      </QueryClientProvider>
    );

    // Initial data
    expect(await screen.findByText('build-manager')).toBeInTheDocument();

    // Update mock data
    mockGetAgentStatus.mockResolvedValue([
      {
        name: 'build-manager',
        status: 'offline',
        tasks: 0,
        memory_usage: 20,
        cpu_usage: 10,
      },
    ]);

    // Force re-render
    rerender(
      <QueryClientProvider client={queryClient}>
        <AgentStatus />
      </QueryClientProvider>
    );

    // Check updated data
    expect(await screen.findByText('offline')).toBeInTheDocument();
    expect(screen.getByText('0 active tasks')).toBeInTheDocument();
    expect(screen.getByText('CPU: 10%')).toBeInTheDocument();
    expect(screen.getByText('Memory: 20%')).toBeInTheDocument();
  });
});