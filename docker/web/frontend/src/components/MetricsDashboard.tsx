import React from 'react';
import {
  Box,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  useColorModeValue,
  Text,
  Heading,
  VStack,
  HStack,
  Progress,
  Icon,
  Tooltip,
  Select,
  Button,
} from '@chakra-ui/react';
import {
  FiActivity,
  FiClock,
  FiCheckCircle,
  FiAlertCircle,
  FiCalendar,
  FiCpu,
  FiHardDrive,
  FiDatabase,
} from 'react-icons/fi';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';

interface MetricsData {
  builds: {
    total: number;
    success: number;
    failure: number;
    avgDuration: number;
    trend: {
      date: string;
      count: number;
      success: number;
      failure: number;
    }[];
  };
  resources: {
    cpu: number;
    memory: number;
    disk: number;
    network: {
      in: number;
      out: number;
    };
  };
  pipelines: {
    active: number;
    completed: number;
    failed: number;
    avgDuration: number;
  };
}

interface MetricsDashboardProps {
  data: MetricsData;
  timeRange: string;
  onTimeRangeChange: (range: string) => void;
  onRefresh: () => void;
}

export const MetricsDashboard: React.FC<MetricsDashboardProps> = ({
  data,
  timeRange,
  onTimeRangeChange,
  onRefresh,
}) => {
  const bgColor = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.600', 'gray.300');

  const successRate = (data.builds.success / data.builds.total) * 100;
  const failureRate = (data.builds.failure / data.builds.total) * 100;

  return (
    <VStack spacing={6} align="stretch">
      <HStack justify="space-between">
        <Heading size="lg">System Metrics</Heading>
        <HStack spacing={4}>
          <Select
            value={timeRange}
            onChange={(e) => onTimeRangeChange(e.target.value)}
            width="200px"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </Select>
          <Button onClick={onRefresh}>Refresh</Button>
        </HStack>
      </HStack>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
        {/* Build Success Rate */}
        <Box
          p={6}
          bg={bgColor}
          borderRadius="lg"
          borderWidth={1}
          borderColor={borderColor}
          boxShadow="sm"
        >
          <Stat>
            <StatLabel>Build Success Rate</StatLabel>
            <StatNumber>{successRate.toFixed(1)}%</StatNumber>
            <StatHelpText>
              <StatArrow type={successRate >= 80 ? 'increase' : 'decrease'} />
              {data.builds.total} total builds
            </StatHelpText>
          </Stat>
          <Progress
            value={successRate}
            colorScheme={successRate >= 80 ? 'green' : 'red'}
            mt={2}
          />
        </Box>

        {/* Average Build Duration */}
        <Box
          p={6}
          bg={bgColor}
          borderRadius="lg"
          borderWidth={1}
          borderColor={borderColor}
          boxShadow="sm"
        >
          <Stat>
            <StatLabel>Avg Build Duration</StatLabel>
            <StatNumber>
              {Math.floor(data.builds.avgDuration / 60)}m{' '}
              {data.builds.avgDuration % 60}s
            </StatNumber>
            <StatHelpText>
              <Icon as={FiClock} mr={1} />
              Per build
            </StatHelpText>
          </Stat>
        </Box>

        {/* Active Pipelines */}
        <Box
          p={6}
          bg={bgColor}
          borderRadius="lg"
          borderWidth={1}
          borderColor={borderColor}
          boxShadow="sm"
        >
          <Stat>
            <StatLabel>Active Pipelines</StatLabel>
            <StatNumber>{data.pipelines.active}</StatNumber>
            <StatHelpText>
              <Icon as={FiActivity} mr={1} />
              {data.pipelines.completed} completed
            </StatHelpText>
          </Stat>
        </Box>

        {/* System Resources */}
        <Box
          p={6}
          bg={bgColor}
          borderRadius="lg"
          borderWidth={1}
          borderColor={borderColor}
          boxShadow="sm"
        >
          <VStack align="stretch" spacing={2}>
            <HStack justify="space-between">
              <Text fontSize="sm" color={textColor}>
                <Icon as={FiCpu} mr={1} />
                CPU
              </Text>
              <Text fontWeight="bold">{data.resources.cpu}%</Text>
            </HStack>
            <Progress value={data.resources.cpu} size="sm" colorScheme="blue" />

            <HStack justify="space-between">
              <Text fontSize="sm" color={textColor}>
                <Icon as={FiDatabase} mr={1} />
                Memory
              </Text>
              <Text fontWeight="bold">{data.resources.memory}%</Text>
            </HStack>
            <Progress
              value={data.resources.memory}
              size="sm"
              colorScheme="purple"
            />

            <HStack justify="space-between">
              <Text fontSize="sm" color={textColor}>
                <Icon as={FiHardDrive} mr={1} />
                Disk
              </Text>
              <Text fontWeight="bold">{data.resources.disk}%</Text>
            </HStack>
            <Progress value={data.resources.disk} size="sm" colorScheme="green" />
          </VStack>
        </Box>
      </SimpleGrid>

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
        {/* Build Trend Chart */}
        <Box
          p={6}
          bg={bgColor}
          borderRadius="lg"
          borderWidth={1}
          borderColor={borderColor}
          boxShadow="sm"
          height="400px"
        >
          <Heading size="md" mb={4}>
            Build Trend
          </Heading>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.builds.trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="success"
                stroke="#48BB78"
                name="Success"
              />
              <Line
                type="monotone"
                dataKey="failure"
                stroke="#F56565"
                name="Failure"
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>

        {/* Resource Usage Chart */}
        <Box
          p={6}
          bg={bgColor}
          borderRadius="lg"
          borderWidth={1}
          borderColor={borderColor}
          boxShadow="sm"
          height="400px"
        >
          <Heading size="md" mb={4}>
            Network Usage
          </Heading>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={[
                {
                  name: 'Network',
                  in: data.resources.network.in,
                  out: data.resources.network.out,
                },
              ]}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              <Bar dataKey="in" fill="#4299E1" name="Inbound" />
              <Bar dataKey="out" fill="#9F7AEA" name="Outbound" />
            </BarChart>
          </ResponsiveContainer>
        </Box>
      </SimpleGrid>
    </VStack>
  );
};