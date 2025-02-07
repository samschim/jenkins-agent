import React, { useState } from 'react';
import {
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  CardActions,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Chip,
} from '@mui/material';

interface Agent {
  type: string;
  description: string;
  status: 'active' | 'inactive';
  tasks: number;
}

const Agents: React.FC = () => {
  const [agents] = useState<Agent[]>([
    {
      type: 'build',
      description: 'Manages Jenkins builds',
      status: 'active',
      tasks: 2,
    },
    {
      type: 'log',
      description: 'Analyzes build logs',
      status: 'active',
      tasks: 1,
    },
    {
      type: 'pipeline',
      description: 'Manages Jenkins pipelines',
      status: 'active',
      tasks: 0,
    },
    {
      type: 'plugin',
      description: 'Manages Jenkins plugins',
      status: 'inactive',
      tasks: 0,
    },
    {
      type: 'user',
      description: 'Manages Jenkins users',
      status: 'active',
      tasks: 1,
    },
  ]);

  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [openDialog, setOpenDialog] = useState(false);

  const handleViewDetails = (agent: Agent) => {
    setSelectedAgent(agent);
    setOpenDialog(true);
  };

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Agents
      </Typography>
      <Grid container spacing={3}>
        {agents.map((agent) => (
          <Grid item xs={12} sm={6} md={4} key={agent.type}>
            <Card>
              <CardHeader
                title={agent.type.charAt(0).toUpperCase() + agent.type.slice(1)}
                subheader={
                  <Chip
                    label={agent.status}
                    color={agent.status === 'active' ? 'success' : 'error'}
                    size="small"
                  />
                }
              />
              <CardContent>
                <Typography variant="body2" color="text.secondary">
                  {agent.description}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Active Tasks: {agent.tasks}
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  color="primary"
                  onClick={() => handleViewDetails(agent)}
                >
                  View Details
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>
          {selectedAgent?.type.charAt(0).toUpperCase() +
            selectedAgent?.type.slice(1)}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            <Typography variant="body1" paragraph>
              Description: {selectedAgent?.description}
            </Typography>
            <Typography variant="body1" paragraph>
              Status: {selectedAgent?.status}
            </Typography>
            <Typography variant="body1" paragraph>
              Active Tasks: {selectedAgent?.tasks}
            </Typography>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default Agents;