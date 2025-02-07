import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Input,
  IconButton,
  Text,
  useColorModeValue,
  Code,
  Spinner,
  useToast,
} from '@chakra-ui/react';
import { FiSend } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatProps {
  onSendMessage: (message: string) => Promise<any>;
}

const Chat: React.FC<ChatProps> = ({ onSendMessage }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const toast = useToast();

  const bgColor = useColorModeValue('gray.50', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    }]);

    setIsLoading(true);
    try {
      const response = await onSendMessage(userMessage);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response,
        timestamp: new Date()
      }]);
    } catch (error) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to send message',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessage = (message: Message) => {
    const isUser = message.role === 'user';
    const align = isUser ? 'flex-end' : 'flex-start';
    const bg = isUser ? 'blue.500' : bgColor;
    const color = isUser ? 'white' : 'inherit';

    return (
      <Box
        key={message.timestamp.toISOString()}
        alignSelf={align}
        maxW="70%"
        p={4}
        borderRadius="lg"
        bg={bg}
        color={color}
        boxShadow="sm"
        borderWidth={1}
        borderColor={borderColor}
      >
        <ReactMarkdown
          components={{
            code({ node, inline, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '');
              return !inline && match ? (
                <SyntaxHighlighter
                  style={tomorrow}
                  language={match[1]}
                  PreTag="div"
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              ) : (
                <Code {...props}>{children}</Code>
              );
            },
          }}
        >
          {message.content}
        </ReactMarkdown>
        <Text
          fontSize="xs"
          color={isUser ? 'whiteAlpha.700' : 'gray.500'}
          mt={2}
        >
          {message.timestamp.toLocaleTimeString()}
        </Text>
      </Box>
    );
  };

  return (
    <VStack h="100%" spacing={4}>
      <VStack
        flex={1}
        w="100%"
        overflowY="auto"
        spacing={4}
        p={4}
        alignItems="stretch"
      >
        {messages.map(renderMessage)}
        <div ref={messagesEndRef} />
      </VStack>

      <HStack
        as="form"
        onSubmit={handleSubmit}
        w="100%"
        p={4}
        borderTopWidth={1}
        borderColor={borderColor}
        bg={bgColor}
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={isLoading}
        />
        <IconButton
          type="submit"
          aria-label="Send message"
          icon={isLoading ? <Spinner /> : <FiSend />}
          colorScheme="blue"
          disabled={isLoading}
        />
      </HStack>
    </VStack>
  );
};

export default Chat;