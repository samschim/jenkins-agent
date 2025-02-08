# Frontend Development Guide

This guide provides detailed information about the frontend architecture, components, and development workflow.

## 🏗️ Architecture

### Tech Stack
- React with TypeScript
- Chakra UI for components
- React Query for data fetching
- React Router for routing
- WebSocket for real-time updates
- Recharts for data visualization

### Directory Structure
```
frontend/
├── src/
│   ├── components/       # Reusable components
│   │   ├── common/      # Common UI components
│   │   ├── pipeline/    # Pipeline-related components
│   │   ├── build/       # Build-related components
│   │   └── metrics/     # Metrics and monitoring components
│   ├── pages/           # Page components
│   ├── hooks/           # Custom React hooks
│   ├── api/             # API client and types
│   ├── utils/           # Utility functions
│   ├── theme/           # Theme configuration
│   └── types/           # TypeScript type definitions
├── public/              # Static assets
└── tests/               # Test files
```

## 🧩 Components

### Pipeline Builder
```typescript
import { PipelineBuilder } from '../components/PipelineBuilder';

// Usage
<PipelineBuilder
  onSave={async (pipeline) => {
    await savePipeline(pipeline);
  }}
  templates={pipelineTemplates}
  plugins={availablePlugins}
/>
```

Features:
- Drag-and-drop stage management
- Stage configuration
- Command management
- Pipeline code generation
- Syntax highlighting

### Log Viewer
```typescript
import { LogViewer } from '../components/LogViewer';

// Usage
<LogViewer
  logs={buildLogs}
  title="Build #123 Logs"
  downloadFileName="build-123.log"
/>
```

Features:
- ANSI color support
- Search functionality
- Log level filtering
- Auto-scroll
- Download/copy options

### Build History
```typescript
import { BuildHistory } from '../components/BuildHistory';

// Usage
<BuildHistory
  builds={builds}
  onRetry={handleRetry}
  onStop={handleStop}
/>
```

Features:
- Detailed build information
- Status indicators
- Build actions
- Log viewing
- Commit information

### Metrics Dashboard
```typescript
import { MetricsDashboard } from '../components/MetricsDashboard';

// Usage
<MetricsDashboard
  data={metricsData}
  timeRange={timeRange}
  onTimeRangeChange={handleTimeRangeChange}
  onRefresh={handleRefresh}
/>
```

Features:
- Real-time metrics
- Interactive charts
- Resource monitoring
- Build trends
- Network usage

## 🔄 State Management

### API Client
```typescript
// api/client.ts
import axios from 'axios';

export const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### React Query Usage
```typescript
// hooks/useBuilds.ts
import { useQuery, useMutation } from 'react-query';
import { api } from '../api/client';

export const useBuilds = () => {
  return useQuery('builds', async () => {
    const { data } = await api.get('/builds');
    return data;
  });
};

export const useStartBuild = () => {
  return useMutation(async (buildConfig) => {
    const { data } = await api.post('/builds', buildConfig);
    return data;
  });
};
```

## 🔌 WebSocket Integration

### WebSocket Hook
```typescript
// hooks/useWebSocket.ts
import { useWebSocket } from 'react-use-websocket';

export const useJenkinsWebSocket = () => {
  const { sendMessage, lastMessage, readyState } = useWebSocket(
    'ws://localhost:8000/ws'
  );

  return {
    sendMessage,
    lastMessage,
    isConnected: readyState === 1,
  };
};
```

### Real-time Updates
```typescript
// components/BuildMonitor.tsx
const BuildMonitor: React.FC = () => {
  const { lastMessage, isConnected } = useJenkinsWebSocket();

  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);
      // Handle real-time updates
    }
  }, [lastMessage]);

  return (
    <Box>
      <Badge colorScheme={isConnected ? 'green' : 'red'}>
        {isConnected ? 'Connected' : 'Disconnected'}
      </Badge>
      {/* Build status display */}
    </Box>
  );
};
```

## 🎨 Theming

### Theme Configuration
```typescript
// theme/index.ts
import { extendTheme } from '@chakra-ui/react';

export const theme = extendTheme({
  config: {
    initialColorMode: 'light',
    useSystemColorMode: true,
  },
  colors: {
    brand: {
      50: '#E6F6FF',
      100: '#BAE3FF',
      // ...
    },
  },
  components: {
    Button: {
      defaultProps: {
        colorScheme: 'brand',
      },
    },
  },
});
```

### Custom Components
```typescript
// components/common/Card.tsx
import { Box, BoxProps } from '@chakra-ui/react';

export const Card: React.FC<BoxProps> = (props) => (
  <Box
    bg={useColorModeValue('white', 'gray.800')}
    borderRadius="lg"
    boxShadow="sm"
    p={6}
    {...props}
  />
);
```

## 📱 Responsive Design

### Breakpoints
```typescript
const breakpoints = {
  sm: '30em',    // 480px
  md: '48em',    // 768px
  lg: '62em',    // 992px
  xl: '80em',    // 1280px
  '2xl': '96em', // 1536px
};
```

### Responsive Components
```typescript
// components/Dashboard.tsx
<SimpleGrid
  columns={{
    base: 1,    // 0-480px
    md: 2,      // 768px-992px
    lg: 3,      // 992px-1280px
    xl: 4       // 1280px+
  }}
  spacing={6}
>
  {/* Dashboard cards */}
</SimpleGrid>
```

## 🧪 Testing

### Component Testing
```typescript
// tests/components/PipelineBuilder.test.tsx
import { render, fireEvent, waitFor } from '@testing-library/react';
import { PipelineBuilder } from '../../components/PipelineBuilder';

describe('PipelineBuilder', () => {
  it('should add a new stage', async () => {
    const { getByText, getAllByRole } = render(<PipelineBuilder />);
    
    fireEvent.click(getByText('Add Stage'));
    
    await waitFor(() => {
      expect(getAllByRole('listitem')).toHaveLength(1);
    });
  });
});
```

### Hook Testing
```typescript
// tests/hooks/useBuilds.test.ts
import { renderHook } from '@testing-library/react-hooks';
import { useBuilds } from '../../hooks/useBuilds';

describe('useBuilds', () => {
  it('should fetch builds', async () => {
    const { result, waitForNextUpdate } = renderHook(() => useBuilds());
    
    await waitForNextUpdate();
    
    expect(result.current.data).toBeDefined();
  });
});
```

## 🔒 Security

### Authentication
```typescript
// utils/auth.ts
export const isAuthenticated = () => {
  const token = localStorage.getItem('token');
  if (!token) return false;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp > Date.now() / 1000;
  } catch {
    return false;
  }
};
```

### Protected Routes
```typescript
// components/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom';

export const ProtectedRoute: React.FC = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" />;
  }
  
  return children;
};
```

## 📦 Build and Deployment

### Production Build
```bash
# Install dependencies
npm install

# Build for production
npm run build

# Test production build
serve -s build
```

### Docker Build
```dockerfile
# Build stage
FROM node:16 as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🔧 Development Workflow

1. **Setup Development Environment**
   ```bash
   # Install dependencies
   npm install
   
   # Start development server
   npm start
   ```

2. **Code Style**
   ```bash
   # Format code
   npm run format
   
   # Lint code
   npm run lint
   ```

3. **Testing**
   ```bash
   # Run tests
   npm test
   
   # Run tests with coverage
   npm test -- --coverage
   ```

4. **Building**
   ```bash
   # Create production build
   npm run build
   
   # Analyze bundle size
   npm run analyze
   ```

## 🐛 Debugging

### React Developer Tools
1. Install React Developer Tools browser extension
2. Use React tab in browser dev tools
3. Monitor component props and state

### Performance Monitoring
```typescript
import { Profiler } from 'react';

<Profiler
  id="BuildHistory"
  onRender={(id, phase, actualDuration) => {
    console.log(`${id} took ${actualDuration}ms to ${phase}`);
  }}
>
  <BuildHistory builds={builds} />
</Profiler>
```

### Error Boundaries
```typescript
// components/ErrorBoundary.tsx
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorDisplay error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

## 📚 Additional Resources

1. [React Documentation](https://reactjs.org/docs)
2. [Chakra UI Documentation](https://chakra-ui.com/docs)
3. [React Query Documentation](https://react-query.tanstack.com/docs)
4. [TypeScript Documentation](https://www.typescriptlang.org/docs)