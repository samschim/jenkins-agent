import { useEffect, useCallback, useRef } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';

export const useTerminalWebSocket = () => {
  const socketUrl = `ws://${window.location.host}/ws/terminal`;
  const { sendMessage, lastMessage, readyState } = useWebSocket(socketUrl, {
    onOpen: () => console.log('WebSocket Connected'),
    onClose: () => console.log('WebSocket Disconnected'),
    onError: (error) => console.error('WebSocket Error:', error),
    shouldReconnect: (closeEvent) => true,
    reconnectAttempts: 10,
    reconnectInterval: 3000,
  });

  const connectionStatus = {
    [ReadyState.CONNECTING]: 'Connecting',
    [ReadyState.OPEN]: 'Connected',
    [ReadyState.CLOSING]: 'Closing',
    [ReadyState.CLOSED]: 'Closed',
    [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
  }[readyState];

  return {
    sendMessage,
    lastMessage,
    readyState,
    connectionStatus,
  };
};