import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Button,
  HStack,
  Input,
  Text,
  VStack,
  useColorModeValue,
  IconButton,
  Tooltip,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Badge,
  useClipboard,
  useToast,
} from '@chakra-ui/react';
import {
  FiDownload,
  FiCopy,
  FiSearch,
  FiFilter,
  FiChevronDown,
  FiArrowUp,
  FiArrowDown,
} from 'react-icons/fi';
import { AnsiUp } from 'ansi_up';

interface LogViewerProps {
  logs: string;
  title?: string;
  downloadFileName?: string;
}

export const LogViewer: React.FC<LogViewerProps> = ({
  logs,
  title = 'Build Logs',
  downloadFileName = 'build.log',
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredLogs, setFilteredLogs] = useState<string[]>([]);
  const [highlightedLines, setHighlightedLines] = useState<number[]>([]);
  const [currentHighlight, setCurrentHighlight] = useState(-1);
  const [logLevel, setLogLevel] = useState<string>('all');
  const [autoScroll, setAutoScroll] = useState(true);

  const logRef = useRef<HTMLDivElement>(null);
  const ansiUp = new AnsiUp();
  const toast = useToast();
  const { onCopy } = useClipboard(logs);

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    const logLines = logs.split('\n');
    let filtered = logLines;

    // Apply log level filter
    if (logLevel !== 'all') {
      filtered = filtered.filter((line) =>
        line.toLowerCase().includes(`[${logLevel}]`)
      );
    }

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter((line) =>
        line.toLowerCase().includes(searchTerm.toLowerCase())
      );
      const highlights = filtered.map((_, index) => index);
      setHighlightedLines(highlights);
      setCurrentHighlight(highlights.length > 0 ? 0 : -1);
    } else {
      setHighlightedLines([]);
      setCurrentHighlight(-1);
    }

    setFilteredLogs(filtered);
  }, [logs, searchTerm, logLevel]);

  useEffect(() => {
    if (autoScroll && logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [filteredLogs, autoScroll]);

  const handleDownload = () => {
    const blob = new Blob([logs], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = downloadFileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const handleCopy = () => {
    onCopy();
    toast({
      title: 'Copied to clipboard',
      status: 'success',
      duration: 2000,
    });
  };

  const navigateHighlight = (direction: 'up' | 'down') => {
    if (highlightedLines.length === 0) return;

    let newIndex;
    if (direction === 'up') {
      newIndex =
        currentHighlight > 0 ? currentHighlight - 1 : highlightedLines.length - 1;
    } else {
      newIndex =
        currentHighlight < highlightedLines.length - 1 ? currentHighlight + 1 : 0;
    }

    setCurrentHighlight(newIndex);
    const element = document.getElementById(`log-line-${highlightedLines[newIndex]}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  return (
    <VStack spacing={4} align="stretch">
      <HStack justify="space-between">
        <Text fontSize="lg" fontWeight="bold">
          {title}
        </Text>
        <HStack spacing={2}>
          <Tooltip label="Download logs">
            <IconButton
              aria-label="Download logs"
              icon={<FiDownload />}
              onClick={handleDownload}
            />
          </Tooltip>
          <Tooltip label="Copy logs">
            <IconButton
              aria-label="Copy logs"
              icon={<FiCopy />}
              onClick={handleCopy}
            />
          </Tooltip>
          <Menu>
            <MenuButton as={Button} rightIcon={<FiChevronDown />}>
              <FiFilter /> Level
            </MenuButton>
            <MenuList>
              <MenuItem onClick={() => setLogLevel('all')}>All</MenuItem>
              <MenuItem onClick={() => setLogLevel('info')}>Info</MenuItem>
              <MenuItem onClick={() => setLogLevel('warn')}>Warning</MenuItem>
              <MenuItem onClick={() => setLogLevel('error')}>Error</MenuItem>
              <MenuItem onClick={() => setLogLevel('debug')}>Debug</MenuItem>
            </MenuList>
          </Menu>
          <HStack>
            <Input
              placeholder="Search logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              width="200px"
            />
            {highlightedLines.length > 0 && (
              <HStack spacing={1}>
                <IconButton
                  aria-label="Previous match"
                  icon={<FiArrowUp />}
                  size="sm"
                  onClick={() => navigateHighlight('up')}
                />
                <Badge>
                  {currentHighlight + 1}/{highlightedLines.length}
                </Badge>
                <IconButton
                  aria-label="Next match"
                  icon={<FiArrowDown />}
                  size="sm"
                  onClick={() => navigateHighlight('down')}
                />
              </HStack>
            )}
          </HStack>
          <Button
            size="sm"
            variant={autoScroll ? 'solid' : 'outline'}
            onClick={() => setAutoScroll(!autoScroll)}
          >
            Auto-scroll
          </Button>
        </HStack>
      </HStack>

      <Box
        ref={logRef}
        height="600px"
        overflowY="auto"
        bg={bgColor}
        borderWidth={1}
        borderColor={borderColor}
        borderRadius="md"
        p={4}
        fontFamily="mono"
        fontSize="sm"
        whiteSpace="pre-wrap"
        css={{
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: useColorModeValue('gray.100', 'gray.800'),
          },
          '&::-webkit-scrollbar-thumb': {
            background: useColorModeValue('gray.300', 'gray.600'),
            borderRadius: '4px',
          },
        }}
      >
        {filteredLogs.map((line, index) => (
          <Box
            key={index}
            id={`log-line-${index}`}
            py={0.5}
            bg={
              highlightedLines.includes(index)
                ? currentHighlight === index
                  ? 'yellow.200'
                  : 'yellow.100'
                : 'transparent'
            }
            dangerouslySetInnerHTML={{ __html: ansiUp.ansi_to_html(line) }}
          />
        ))}
      </Box>
    </VStack>
  );
};