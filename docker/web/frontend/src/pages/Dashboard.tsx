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
  Icon,
  Progress,
} from '@chakra-ui/react';
import {
  FiActivity,
  FiClock,
  FiCheckCircle,
  FiAlertCircle,
} from 'react-icons/fi';
import { useQuery } from 'react-query';
import { fetchMetrics } from '../api/metrics';

export const Dashboard = () => {
  const { data: metrics, isLoading, error } = useQuery('metrics', fetchMetrics);
  const bgColor = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  if (isLoading) {
    return <Progress size="xs" isIndeterminate />;
  }

  if (error) {
    return (
      <Box p={4} bg="red.100" color="red.900" borderRadius="md">
        Error loading metrics: {(error as Error).message}
      </Box>
    );
  }

  if (!metrics) {
    return null;
  }

  const buildSuccessRate = (metrics.builds.successful_builds / metrics.builds.total_builds) * 100;
  const pipelineSuccessRate = (metrics.pipelines.successful_runs / metrics.pipelines.total_runs) * 100;

  return (
    <VStack spacing={8} align="stretch">
      <Heading size="lg">Dashboard</Heading>

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
            <StatNumber>{buildSuccessRate.toFixed(1)}%</StatNumber>
            <StatHelpText>
              <StatArrow type={buildSuccessRate >= 80 ? 'increase' : 'decrease'} />
              {metrics.builds.total_builds} total builds
            </StatHelpText>
          </Stat>
          <Progress
            value={buildSuccessRate}
            colorScheme={buildSuccessRate >= 80 ? 'green' : 'red'}
            mt={2}
          />
        </Box>

        {/* Pipeline Success Rate */}
        <Box
          p={6}
          bg={bgColor}
          borderRadius="lg"
          borderWidth={1}
          borderColor={borderColor}
          boxShadow="sm"
        >
          <Stat>
            <StatLabel>Pipeline Success Rate</StatLabel>
            <StatNumber>{pipelineSuccessRate.toFixed(1)}%</StatNumber>
            <StatHelpText>
              <StatArrow type={pipelineSuccessRate >= 80 ? 'increase' : 'decrease'} />
              {metrics.pipelines.total_runs} total runs
            </StatHelpText>
          </Stat>
          <Progress
            value={pipelineSuccessRate}
            colorScheme={pipelineSuccessRate >= 80 ? 'green' : 'red'}
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
              {(metrics.builds.average_duration / 60).toFixed(1)}m
            </StatNumber>
            <StatHelpText>
              <Icon as={FiClock} mr={1} />
              Per build
            </StatHelpText>
          </Stat>
        </Box>

        {/* Build Frequency */}
        <Box
          p={6}
          bg={bgColor}
          borderRadius="lg"
          borderWidth={1}
          borderColor={borderColor}
          boxShadow="sm"
        >
          <Stat>
            <StatLabel>Build Frequency</StatLabel>
            <StatNumber>
              {metrics.builds.build_frequency.toFixed(1)}/day
            </StatNumber>
            <StatHelpText>
              <Icon as={FiActivity} mr={1} />
              Average builds per day
            </StatHelpText>
          </Stat>
        </Box>
      </SimpleGrid>

      {/* Recommendations */}
      {metrics.recommendations && metrics.recommendations.length > 0 && (
        <Box
          p={6}
          bg={bgColor}
          borderRadius="lg"
          borderWidth={1}
          borderColor={borderColor}
          boxShadow="sm"
        >
          <Heading size="md" mb={4}>
            Recommendations
          </Heading>
          <VStack align="stretch" spacing={3}>
            {metrics.recommendations.map((rec, index) => (
              <HStack key={index} spacing={3}>
                <Icon
                  as={rec.includes('error') ? FiAlertCircle : FiCheckCircle}
                  color={rec.includes('error') ? 'red.500' : 'green.500'}
                />
                <Text>{rec}</Text>
              </HStack>
            ))}
          </VStack>
        </Box>
      )}
    </VStack>
  );
};