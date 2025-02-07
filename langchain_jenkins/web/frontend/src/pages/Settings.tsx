import React, { useState } from 'react';
import {
  Typography,
  Paper,
  TextField,
  Button,
  Grid,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Snackbar,
} from '@mui/material';

interface Settings {
  jenkinsUrl: string;
  jenkinsUser: string;
  jenkinsToken: string;
  enableWebSocket: boolean;
  enableCache: boolean;
  cacheTimeout: number;
  logLevel: string;
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<Settings>({
    jenkinsUrl: 'http://localhost:8080',
    jenkinsUser: '',
    jenkinsToken: '',
    enableWebSocket: true,
    enableCache: true,
    cacheTimeout: 300,
    logLevel: 'INFO',
  });

  const [showSuccess, setShowSuccess] = useState(false);

  const handleChange = (field: keyof Settings) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value =
      event.target.type === 'checkbox'
        ? event.target.checked
        : event.target.value;
    setSettings({ ...settings, [field]: value });
  };

  const handleSave = () => {
    // TODO: Save settings to backend
    setShowSuccess(true);
  };

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Jenkins Configuration
            </Typography>
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Jenkins URL"
              value={settings.jenkinsUrl}
              onChange={handleChange('jenkinsUrl')}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Jenkins Username"
              value={settings.jenkinsUser}
              onChange={handleChange('jenkinsUser')}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="password"
              label="Jenkins API Token"
              value={settings.jenkinsToken}
              onChange={handleChange('jenkinsToken')}
            />
          </Grid>

          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="h6" gutterBottom>
              Application Settings
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.enableWebSocket}
                  onChange={handleChange('enableWebSocket')}
                />
              }
              label="Enable WebSocket"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.enableCache}
                  onChange={handleChange('enableCache')}
                />
              }
              label="Enable Cache"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Cache Timeout (seconds)"
              value={settings.cacheTimeout}
              onChange={handleChange('cacheTimeout')}
              disabled={!settings.enableCache}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              select
              label="Log Level"
              value={settings.logLevel}
              onChange={handleChange('logLevel')}
              SelectProps={{
                native: true,
              }}
            >
              <option value="DEBUG">DEBUG</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
            </TextField>
          </Grid>

          <Grid item xs={12}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleSave}
              sx={{ mt: 2 }}
            >
              Save Settings
            </Button>
          </Grid>
        </Grid>
      </Paper>

      <Snackbar
        open={showSuccess}
        autoHideDuration={6000}
        onClose={() => setShowSuccess(false)}
      >
        <Alert
          onClose={() => setShowSuccess(false)}
          severity="success"
          sx={{ width: '100%' }}
        >
          Settings saved successfully!
        </Alert>
      </Snackbar>
    </div>
  );
};

export default Settings;