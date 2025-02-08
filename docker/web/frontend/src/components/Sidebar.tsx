import React from 'react';
import {
  Box,
  CloseButton,
  Flex,
  Icon,
  Text,
  BoxProps,
  VStack,
} from '@chakra-ui/react';
import { Link, useLocation } from 'react-router-dom';
import {
  FiHome,
  FiTrello,
  FiSettings,
  FiTerminal,
  FiGitBranch,
  FiActivity,
} from 'react-icons/fi';

interface LinkItemProps {
  name: string;
  icon: any;
  path: string;
}

const LinkItems: Array<LinkItemProps> = [
  { name: 'Dashboard', icon: FiHome, path: '/' },
  { name: 'Pipelines', icon: FiGitBranch, path: '/pipelines' },
  { name: 'Jobs', icon: FiTrello, path: '/jobs' },
  { name: 'Terminal', icon: FiTerminal, path: '/terminal' },
  { name: 'Monitoring', icon: FiActivity, path: '/monitoring' },
  { name: 'Settings', icon: FiSettings, path: '/settings' },
];

interface SidebarProps extends BoxProps {
  onClose: () => void;
}

export const Sidebar = ({ onClose, ...rest }: SidebarProps) => {
  const location = useLocation();

  return (
    <Box
      transition="3s ease"
      bg="white"
      borderRight="1px"
      borderRightColor="gray.200"
      w={{ base: 'full', md: 60 }}
      pos="fixed"
      h="full"
      {...rest}
    >
      <Flex h="20" alignItems="center" mx="8" justifyContent="space-between">
        <Text fontSize="2xl" fontWeight="bold">
          Jenkins AI
        </Text>
        <CloseButton display={{ base: 'flex', md: 'none' }} onClick={onClose} />
      </Flex>
      <VStack spacing={4} align="stretch" px={4}>
        {LinkItems.map((link) => (
          <Link key={link.name} to={link.path}>
            <Flex
              align="center"
              p="4"
              mx="4"
              borderRadius="lg"
              role="group"
              cursor="pointer"
              bg={location.pathname === link.path ? 'blue.50' : 'transparent'}
              color={location.pathname === link.path ? 'blue.500' : 'gray.600'}
              _hover={{
                bg: 'blue.50',
                color: 'blue.500',
              }}
            >
              <Icon
                mr="4"
                fontSize="16"
                as={link.icon}
              />
              {link.name}
            </Flex>
          </Link>
        ))}
      </VStack>
    </Box>
  );
};