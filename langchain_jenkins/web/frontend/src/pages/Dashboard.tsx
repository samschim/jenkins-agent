import React from 'react';
import { Grid, Typography } from '@mui/material';
import AgentStatus from '@/components/dashboard/AgentStatus';
import TaskHistory from '@/components/dashboard/TaskHistory';
import SystemMetrics from '@/components/dashboard/SystemMetrics';
import ErrorAnalysis from '@/components/dashboard/ErrorAnalysis';

const Dashboard: React.FC = () => {
  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <AgentStatus />
        </Grid>
        <Grid item xs={12}>
          <SystemMetrics />
        </Grid>
        <Grid item xs={12} md={6}>
          <TaskHistory />
        </Grid>
        <Grid item xs={12} md={6}>
          <ErrorAnalysis />
        </Grid>
      </Grid>
    </div>
  );
};

export default Dashboard;