import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Grid,
  Typography,
  Chip,
  Box,
  LinearProgress,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { getAgentStatus } from '@/services/api';

interface AgentInfo {
  name: string;
  status: 'online' | 'offline' | 'busy';
  tasks: number;
  memory_usage: number;
  cpu_usage: number;
}

const AgentStatus: React.FC = () => {
  const { data: agents = [], isLoading } = useQuery<AgentInfo[]>({
    queryKey: ['agents'],
    queryFn: getAgentStatus,
    refetchInterval: 5000,
  });

  if (isLoading) {
    return <LinearProgress />;
  }

  return (
    <Card>
      <CardHeader title="Agent Status" />
      <CardContent>
        <Grid container spacing={2}>
          {agents.map((agent) => (
            <Grid item xs={12} key={agent.name}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  mb: 2,
                }}
              >
                <Box>
                  <Typography variant="subtitle1">{agent.name}</Typography>
                  <Chip
                    label={agent.status}
                    color={
                      agent.status === 'online'
                        ? 'success'
                        : agent.status === 'busy'
                        ? 'warning'
                        : 'error'
                    }
                    size="small"
                    sx={{ mr: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    {agent.tasks} active tasks
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    CPU: {agent.cpu_usage}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={agent.cpu_usage}
                    sx={{ mb: 1, width: 100 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    Memory: {agent.memory_usage}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={agent.memory_usage}
                    sx={{ width: 100 }}
                  />
                </Box>
              </Box>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default AgentStatus;