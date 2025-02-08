import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  VStack,
  Input,
  Text,
  useColorModeValue,
  IconButton,
  HStack,
  useToast,
} from '@chakra-ui/react';
import { FiSend } from 'react-icons/fi';
import { useWebSocket } from '../hooks/useWebSocket';

export const Terminal = () => {
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<string[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const toast = useToast();
  const { sendMessage, lastMessage, readyState } = useWebSocket();

  const bgColor = useColorModeValue('gray.900', 'gray.800');
  const textColor = useColorModeValue('green.400', 'green.300');

  useEffect(() => {
    if (lastMessage) {
      try {
        const response = JSON.parse(lastMessage.data);
        setHistory(prev => [...prev, `$ ${response.command}`, response.output]);
      } catch (e) {
        setHistory(prev => [...prev, lastMessage.data]);
      }
    }
  }, [lastMessage]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    if (readyState !== 1) {
      toast({
        title: 'Connection Error',
        description: 'Not connected to server',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    sendMessage(input);
    setInput('');
  };

  return (
    <VStack spacing={4} align="stretch">
      <Box
        bg={bgColor}
        color={textColor}
        p={4}
        borderRadius="md"
        fontFamily="mono"
        minH="60vh"
        maxH="60vh"
        overflowY="auto"
      >
        {history.map((line, i) => (
          <Text key={i} whiteSpace="pre-wrap">
            {line}
          </Text>
        ))}
        <div ref={bottomRef} />
      </Box>

      <form onSubmit={handleSubmit}>
        <HStack>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter command..."
            fontFamily="mono"
            bg={bgColor}
            color={textColor}
            borderColor="gray.600"
            _hover={{ borderColor: 'gray.500' }}
            _focus={{ borderColor: 'blue.500' }}
          />
          <IconButton
            type="submit"
            aria-label="Send command"
            icon={<FiSend />}
            colorScheme="blue"
          />
        </HStack>
      </form>
    </VStack>
  );
};