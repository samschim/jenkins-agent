import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Typography,
  Chip,
  Box,
} from '@mui/material';
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Schedule as PendingIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { getTaskHistory } from '@/services/api';
import { formatDistanceToNow } from 'date-fns';

interface TaskInfo {
  id: string;
  description: string;
  status: 'success' | 'error' | 'pending';
  agent: string;
  created_at: string;
  completed_at?: string;
  error_message?: string;
}

const TaskHistory: React.FC = () => {
  const { data: tasks = [], isLoading } = useQuery<TaskInfo[]>({
    queryKey: ['tasks'],
    queryFn: getTaskHistory,
    refetchInterval: 5000,
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <SuccessIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <PendingIcon color="warning" />;
    }
  };

  return (
    <Card>
      <CardHeader title="Task History" />
      <CardContent>
        <List>
          {tasks.map((task) => (
            <ListItem key={task.id}>
              <ListItemIcon>{getStatusIcon(task.status)}</ListItemIcon>
              <ListItemText
                primary={task.description}
                secondary={
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Agent: {task.agent}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {task.completed_at
                        ? `Completed ${formatDistanceToNow(
                            new Date(task.completed_at),
                            { addSuffix: true }
                          )}`
                        : `Started ${formatDistanceToNow(
                            new Date(task.created_at),
                            { addSuffix: true }
                          )}`}
                    </Typography>
                    {task.error_message && (
                      <Typography variant="body2" color="error">
                        Error: {task.error_message}
                      </Typography>
                    )}
                  </Box>
                }
              />
              <Chip
                label={task.status}
                color={
                  task.status === 'success'
                    ? 'success'
                    : task.status === 'error'
                    ? 'error'
                    : 'warning'
                }
                size="small"
              />
            </ListItem>
          ))}
          {tasks.length === 0 && !isLoading && (
            <ListItem>
              <ListItemText
                primary={
                  <Typography variant="body2" color="text.secondary">
                    No tasks found
                  </Typography>
                }
              />
            </ListItem>
          )}
        </List>
      </CardContent>
    </Card>
  );
};

export default TaskHistory;