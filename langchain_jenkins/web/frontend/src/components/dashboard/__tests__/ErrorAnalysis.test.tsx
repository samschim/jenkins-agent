import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ErrorAnalysis from '../ErrorAnalysis';
import { getErrorAnalysis } from '@/services/api';

// Mock API
jest.mock('@/services/api');
const mockGetErrorAnalysis = getErrorAnalysis as jest.MockedFunction<typeof getErrorAnalysis>;

// Mock Recharts
jest.mock('recharts', () => ({
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => null,
  Cell: () => null,
  Tooltip: () => null,
}));

// Test data
const mockAnalysis = {
  patterns: [
    {
      type: 'OutOfMemoryError',
      count: 5,
      examples: ['Java heap space error in build'],
      solutions: ['Increase heap size'],
    },
    {
      type: 'NullPointerException',
      count: 3,
      examples: ['Null reference in pipeline'],
      solutions: ['Add null checks'],
    },
  ],
  correlations: [
    {
      source: 'OutOfMemoryError',
      target: 'BuildFailure',
      confidence: 0.8,
    },
    {
      source: 'NullPointerException',
      target: 'TestFailure',
      confidence: 0.6,
    },
  ],
  distribution: [
    {
      type: 'OutOfMemoryError',
      value: 50,
    },
    {
      type: 'NullPointerException',
      value: 30,
    },
    {
      type: 'Other',
      value: 20,
    },
  ],
};

describe('ErrorAnalysis', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  beforeEach(() => {
    mockGetErrorAnalysis.mockResolvedValue(mockAnalysis);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders error analysis components', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <ErrorAnalysis />
      </QueryClientProvider>
    );

    // Check title
    expect(screen.getByText('Error Analysis')).toBeInTheDocument();

    // Check section titles
    expect(screen.getByText('Error Distribution')).toBeInTheDocument();
    expect(screen.getByText('Error Patterns')).toBeInTheDocument();
    expect(screen.getByText('Error Correlations')).toBeInTheDocument();

    // Check pie chart
    expect(await screen.findByTestId('pie-chart')).toBeInTheDocument();

    // Check error patterns
    expect(screen.getByText('OutOfMemoryError')).toBeInTheDocument();
    expect(screen.getByText('NullPointerException')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();

    // Check error correlations
    expect(screen.getByText('80.0%')).toBeInTheDocument();
    expect(screen.getByText('60.0%')).toBeInTheDocument();
  });

  it('handles loading state', () => {
    mockGetErrorAnalysis.mockImplementation(() => new Promise(() => {}));

    render(
      <QueryClientProvider client={queryClient}>
        <ErrorAnalysis />
      </QueryClientProvider>
    );

    expect(screen.queryByTestId('pie-chart')).not.toBeInTheDocument();
  });

  it('handles empty data', async () => {
    mockGetErrorAnalysis.mockResolvedValue({
      patterns: [],
      correlations: [],
      distribution: [],
    });

    render(
      <QueryClientProvider client={queryClient}>
        <ErrorAnalysis />
      </QueryClientProvider>
    );

    // Should still render sections
    expect(await screen.findByText('Error Analysis')).toBeInTheDocument();
    expect(screen.getByText('Error Distribution')).toBeInTheDocument();
    expect(screen.getByText('Error Patterns')).toBeInTheDocument();
    expect(screen.getByText('Error Correlations')).toBeInTheDocument();
  });

  it('updates data periodically', async () => {
    const { rerender } = render(
      <QueryClientProvider client={queryClient}>
        <ErrorAnalysis />
      </QueryClientProvider>
    );

    // Initial data
    expect(await screen.findByText('OutOfMemoryError')).toBeInTheDocument();

    // Update mock data
    mockGetErrorAnalysis.mockResolvedValue({
      ...mockAnalysis,
      patterns: [
        {
          type: 'NewError',
          count: 10,
          examples: ['New error type'],
          solutions: ['New solution'],
        },
      ],
    });

    // Force re-render
    rerender(
      <QueryClientProvider client={queryClient}>
        <ErrorAnalysis />
      </QueryClientProvider>
    );

    // Check updated data
    expect(await screen.findByText('NewError')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
  });
});