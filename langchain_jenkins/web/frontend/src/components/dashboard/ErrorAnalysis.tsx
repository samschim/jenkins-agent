import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Grid,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { getErrorAnalysis } from '@/services/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

interface ErrorPattern {
  type: string;
  count: number;
  examples: string[];
  solutions: string[];
}

interface ErrorCorrelation {
  source: string;
  target: string;
  confidence: number;
}

interface ErrorAnalysis {
  patterns: ErrorPattern[];
  correlations: ErrorCorrelation[];
  distribution: {
    type: string;
    value: number;
  }[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const ErrorAnalysis: React.FC = () => {
  const { data: analysis, isLoading } = useQuery<ErrorAnalysis>({
    queryKey: ['errors'],
    queryFn: getErrorAnalysis,
    refetchInterval: 30000,
  });

  if (isLoading || !analysis) {
    return null;
  }

  return (
    <Card>
      <CardHeader title="Error Analysis" />
      <CardContent>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              Error Distribution
            </Typography>
            <Box sx={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={analysis.distribution}
                    dataKey="value"
                    nameKey="type"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label
                  >
                    {analysis.distribution.map((entry, index) => (
                      <Cell
                        key={entry.type}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              Error Patterns
            </Typography>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell align="right">Count</TableCell>
                    <TableCell>Example</TableCell>
                    <TableCell>Solution</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {analysis.patterns.map((pattern) => (
                    <TableRow key={pattern.type}>
                      <TableCell component="th" scope="row">
                        {pattern.type}
                      </TableCell>
                      <TableCell align="right">{pattern.count}</TableCell>
                      <TableCell>
                        {pattern.examples[0]?.substring(0, 50)}...
                      </TableCell>
                      <TableCell>
                        {pattern.solutions[0]?.substring(0, 50)}...
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>
          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              Error Correlations
            </Typography>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Source Error</TableCell>
                    <TableCell>Related Error</TableCell>
                    <TableCell align="right">Confidence</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {analysis.correlations.map((correlation, index) => (
                    <TableRow key={index}>
                      <TableCell>{correlation.source}</TableCell>
                      <TableCell>{correlation.target}</TableCell>
                      <TableCell align="right">
                        {(correlation.confidence * 100).toFixed(1)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default ErrorAnalysis;