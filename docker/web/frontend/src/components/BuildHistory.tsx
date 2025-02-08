import React, { useState } from 'react';
import {
  Box,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useColorModeValue,
  Text,
  HStack,
  VStack,
  Progress,
  Tooltip,
  Button,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
} from '@chakra-ui/react';
import {
  FiMoreVertical,
  FiPlay,
  FiStop,
  FiClock,
  FiCalendar,
  FiUser,
  FiGitCommit,
} from 'react-icons/fi';
import { format, formatDistanceToNow } from 'date-fns';
import { LogViewer } from './LogViewer';

interface Build {
  id: number;
  status: 'success' | 'failure' | 'running' | 'pending' | 'cancelled';
  startTime: Date;
  duration: number;
  trigger: string;
  commit: {
    hash: string;
    message: string;
    author: string;
  };
  logs?: string;
}

interface BuildHistoryProps {
  builds: Build[];
  onRetry?: (buildId: number) => void;
  onStop?: (buildId: number) => void;
}

export const BuildHistory: React.FC<BuildHistoryProps> = ({
  builds,
  onRetry,
  onStop,
}) => {
  const [selectedBuild, setSelectedBuild] = useState<Build | null>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();

  const getBadgeColor = (status: Build['status']) => {
    switch (status) {
      case 'success':
        return 'green';
      case 'failure':
        return 'red';
      case 'running':
        return 'blue';
      case 'pending':
        return 'yellow';
      case 'cancelled':
        return 'gray';
      default:
        return 'gray';
    }
  };

  const handleViewLogs = (build: Build) => {
    setSelectedBuild(build);
    onOpen();
  };

  return (
    <Box>
      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>#</Th>
            <Th>Status</Th>
            <Th>Commit</Th>
            <Th>Trigger</Th>
            <Th>Started</Th>
            <Th>Duration</Th>
            <Th>Actions</Th>
          </Tr>
        </Thead>
        <Tbody>
          {builds.map((build) => (
            <Tr key={build.id}>
              <Td>#{build.id}</Td>
              <Td>
                <Badge colorScheme={getBadgeColor(build.status)}>
                  {build.status.toUpperCase()}
                </Badge>
                {build.status === 'running' && (
                  <Progress
                    size="xs"
                    isIndeterminate
                    colorScheme="blue"
                    mt={2}
                  />
                )}
              </Td>
              <Td>
                <VStack align="start" spacing={1}>
                  <HStack>
                    <Text fontSize="sm" fontFamily="mono">
                      {build.commit.hash.substring(0, 7)}
                    </Text>
                    <Text fontSize="sm" noOfLines={1}>
                      {build.commit.message}
                    </Text>
                  </HStack>
                  <HStack fontSize="xs" color="gray.500">
                    <FiUser />
                    <Text>{build.commit.author}</Text>
                  </HStack>
                </VStack>
              </Td>
              <Td>{build.trigger}</Td>
              <Td>
                <Tooltip
                  label={format(build.startTime, 'PPpp')}
                  placement="top"
                >
                  <Text>
                    {formatDistanceToNow(build.startTime, { addSuffix: true })}
                  </Text>
                </Tooltip>
              </Td>
              <Td>
                <HStack>
                  <FiClock />
                  <Text>
                    {Math.floor(build.duration / 60)}m {build.duration % 60}s
                  </Text>
                </HStack>
              </Td>
              <Td>
                <HStack spacing={2}>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleViewLogs(build)}
                  >
                    View Logs
                  </Button>
                  {build.status === 'running' && onStop && (
                    <IconButton
                      aria-label="Stop build"
                      icon={<FiStop />}
                      size="sm"
                      colorScheme="red"
                      variant="ghost"
                      onClick={() => onStop(build.id)}
                    />
                  )}
                  {(build.status === 'failure' ||
                    build.status === 'cancelled') &&
                    onRetry && (
                      <IconButton
                        aria-label="Retry build"
                        icon={<FiPlay />}
                        size="sm"
                        colorScheme="green"
                        variant="ghost"
                        onClick={() => onRetry(build.id)}
                      />
                    )}
                  <Menu>
                    <MenuButton
                      as={IconButton}
                      aria-label="More options"
                      icon={<FiMoreVertical />}
                      variant="ghost"
                      size="sm"
                    />
                    <MenuList>
                      <MenuItem
                        icon={<FiGitCommit />}
                        onClick={() =>
                          window.open(
                            `https://github.com/owner/repo/commit/${build.commit.hash}`,
                            '_blank'
                          )
                        }
                      >
                        View Commit
                      </MenuItem>
                      <MenuItem
                        icon={<FiCalendar />}
                        onClick={() =>
                          window.open(
                            `https://github.com/owner/repo/actions/runs/${build.id}`,
                            '_blank'
                          )
                        }
                      >
                        View in GitHub Actions
                      </MenuItem>
                    </MenuList>
                  </Menu>
                </HStack>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>

      <Modal isOpen={isOpen} onClose={onClose} size="6xl">
        <ModalOverlay />
        <ModalContent maxH="90vh">
          <ModalHeader>
            Build #{selectedBuild?.id} Logs
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody overflow="hidden">
            {selectedBuild?.logs && <LogViewer logs={selectedBuild.logs} />}
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};