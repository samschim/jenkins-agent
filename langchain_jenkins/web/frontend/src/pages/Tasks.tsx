import React, { useState } from 'react';
import {
  Button,
  TextField,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';

interface Task {
  id: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  agent: string;
}

const Tasks: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [newTask, setNewTask] = useState('');
  const [selectedAgent, setSelectedAgent] = useState('');

  const handleAddTask = () => {
    if (newTask && selectedAgent) {
      const task: Task = {
        id: Math.random().toString(36).substr(2, 9),
        description: newTask,
        status: 'pending',
        agent: selectedAgent,
      };
      setTasks([...tasks, task]);
      setNewTask('');
      setSelectedAgent('');
      setOpenDialog(false);
    }
  };

  const handleStartTask = (taskId: string) => {
    setTasks(
      tasks.map((task) =>
        task.id === taskId ? { ...task, status: 'running' } : task
      )
    );
  };

  const handleStopTask = (taskId: string) => {
    setTasks(
      tasks.map((task) =>
        task.id === taskId ? { ...task, status: 'completed' } : task
      )
    );
  };

  const handleDeleteTask = (taskId: string) => {
    setTasks(tasks.filter((task) => task.id !== taskId));
  };

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Tasks
      </Typography>
      <Button
        variant="contained"
        color="primary"
        onClick={() => setOpenDialog(true)}
        sx={{ mb: 2 }}
      >
        New Task
      </Button>
      <Paper>
        <List>
          {tasks.map((task) => (
            <ListItem key={task.id}>
              <ListItemText
                primary={task.description}
                secondary={`Status: ${task.status} | Agent: ${task.agent}`}
              />
              <ListItemSecondaryAction>
                {task.status === 'pending' && (
                  <IconButton
                    edge="end"
                    aria-label="start"
                    onClick={() => handleStartTask(task.id)}
                  >
                    <PlayIcon />
                  </IconButton>
                )}
                {task.status === 'running' && (
                  <IconButton
                    edge="end"
                    aria-label="stop"
                    onClick={() => handleStopTask(task.id)}
                  >
                    <StopIcon />
                  </IconButton>
                )}
                <IconButton
                  edge="end"
                  aria-label="delete"
                  onClick={() => handleDeleteTask(task.id)}
                >
                  <DeleteIcon />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      </Paper>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>New Task</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Task Description"
            fullWidth
            value={newTask}
            onChange={(e) => setNewTask(e.target.value)}
          />
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Agent</InputLabel>
            <Select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
            >
              <MenuItem value="build">Build Manager</MenuItem>
              <MenuItem value="log">Log Analyzer</MenuItem>
              <MenuItem value="pipeline">Pipeline Manager</MenuItem>
              <MenuItem value="plugin">Plugin Manager</MenuItem>
              <MenuItem value="user">User Manager</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleAddTask} color="primary">
            Add Task
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default Tasks;