import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TaskHistory from '../TaskHistory';
import { getTaskHistory } from '@/services/api';

// Mock API
jest.mock('@/services/api');
const mockGetTaskHistory = getTaskHistory as jest.MockedFunction<typeof getTaskHistory>;

// Test data
const mockTasks = [
  {
    id: '1',
    description: 'Build project',
    status: 'success',
    agent: 'build-manager',
    created_at: '2024-02-07T12:00:00Z',
    completed_at: '2024-02-07T12:05:00Z',
  },
  {
    id: '2',
    description: 'Analyze logs',
    status: 'error',
    agent: 'log-analyzer',
    created_at: '2024-02-07T12:10:00Z',
    completed_at: '2024-02-07T12:11:00Z',
    error_message: 'Failed to analyze logs',
  },
  {
    id: '3',
    description: 'Update pipeline',
    status: 'pending',
    agent: 'pipeline-manager',
    created_at: '2024-02-07T12:15:00Z',
  },
];

describe('TaskHistory', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  beforeEach(() => {
    mockGetTaskHistory.mockResolvedValue(mockTasks);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders task history list', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <TaskHistory />
      </QueryClientProvider>
    );

    // Check title
    expect(screen.getByText('Task History')).toBeInTheDocument();

    // Wait for data to load
    expect(await screen.findByText('Build project')).toBeInTheDocument();
    expect(screen.getByText('Analyze logs')).toBeInTheDocument();
    expect(screen.getByText('Update pipeline')).toBeInTheDocument();

    // Check status chips
    expect(screen.getByText('success')).toBeInTheDocument();
    expect(screen.getByText('error')).toBeInTheDocument();
    expect(screen.getByText('pending')).toBeInTheDocument();

    // Check agents
    expect(screen.getByText('Agent: build-manager')).toBeInTheDocument();
    expect(screen.getByText('Agent: log-analyzer')).toBeInTheDocument();
    expect(screen.getByText('Agent: pipeline-manager')).toBeInTheDocument();

    // Check error message
    expect(screen.getByText('Error: Failed to analyze logs')).toBeInTheDocument();
  });

  it('handles empty data', async () => {
    mockGetTaskHistory.mockResolvedValue([]);

    render(
      <QueryClientProvider client={queryClient}>
        <TaskHistory />
      </QueryClientProvider>
    );

    expect(await screen.findByText('No tasks found')).toBeInTheDocument();
  });

  it('updates data periodically', async () => {
    const { rerender } = render(
      <QueryClientProvider client={queryClient}>
        <TaskHistory />
      </QueryClientProvider>
    );

    // Initial data
    expect(await screen.findByText('Build project')).toBeInTheDocument();

    // Update mock data
    mockGetTaskHistory.mockResolvedValue([
      {
        id: '4',
        description: 'New task',
        status: 'success',
        agent: 'build-manager',
        created_at: '2024-02-07T12:20:00Z',
        completed_at: '2024-02-07T12:25:00Z',
      },
    ]);

    // Force re-render
    rerender(
      <QueryClientProvider client={queryClient}>
        <TaskHistory />
      </QueryClientProvider>
    );

    // Check updated data
    expect(await screen.findByText('New task')).toBeInTheDocument();
    expect(screen.queryByText('Build project')).not.toBeInTheDocument();
  });

  it('formats timestamps correctly', async () => {
    const now = new Date();
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);
    const tenMinutesAgo = new Date(now.getTime() - 10 * 60 * 1000);

    mockGetTaskHistory.mockResolvedValue([
      {
        id: '1',
        description: 'Recent task',
        status: 'success',
        agent: 'build-manager',
        created_at: tenMinutesAgo.toISOString(),
        completed_at: fiveMinutesAgo.toISOString(),
      },
    ]);

    render(
      <QueryClientProvider client={queryClient}>
        <TaskHistory />
      </QueryClientProvider>
    );

    // Check time formatting
    expect(await screen.findByText(/Completed 5 minutes ago/)).toBeInTheDocument();
  });
});