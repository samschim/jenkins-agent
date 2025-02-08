import React from 'react';
import {
  Box,
  Flex,
  Drawer,
  DrawerContent,
  useDisclosure,
  Container,
} from '@chakra-ui/react';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isOpen, onOpen, onClose } = useDisclosure();

  return (
    <Box minH="100vh" bg="gray.50">
      <Sidebar
        onClose={() => onClose}
        display={{ base: 'none', md: 'block' }}
      />
      <Drawer
        isOpen={isOpen}
        placement="left"
        onClose={onClose}
        returnFocusOnClose={false}
        onOverlayClick={onClose}
        size="full"
      >
        <DrawerContent>
          <Sidebar onClose={onClose} />
        </DrawerContent>
      </Drawer>
      <Box ml={{ base: 0, md: 60 }} transition=".3s ease">
        <Navbar onOpen={onOpen} />
        <Container maxW="container.xl" py="8">
          <Box
            borderRadius="lg"
            bg="white"
            boxShadow="sm"
            p={4}
          >
            {children}
          </Box>
        </Container>
      </Box>
    </Box>
  );
};