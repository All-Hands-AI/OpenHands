import React, { createContext, useContext, useState, useEffect, ReactNode, useRef } from 'react'
import { io, Socket } from 'socket.io-client'
import { WebSocketMessage } from '../types'

interface WebSocketContextType {
  socket: Socket | null
  isConnected: boolean
  sendMessage: (message: any) => void
  lastMessage: WebSocketMessage | null
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()

  useEffect(() => {
    const connectSocket = () => {
      // Try to connect to local backend first, fallback to mock
      const socketUrl = process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8000' 
        : window.location.origin

      const newSocket = io(socketUrl, {
        transports: ['websocket', 'polling'],
        timeout: 5000,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
      })

      newSocket.on('connect', () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current)
        }
      })

      newSocket.on('disconnect', () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        
        // Auto-reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...')
          newSocket.connect()
        }, 3000)
      })

      newSocket.on('message', (data: any) => {
        const message: WebSocketMessage = {
          type: 'message',
          data,
          timestamp: new Date(),
        }
        setLastMessage(message)
      })

      newSocket.on('system_info', (data: any) => {
        const message: WebSocketMessage = {
          type: 'system_info',
          data,
          timestamp: new Date(),
        }
        setLastMessage(message)
      })

      newSocket.on('terminal_output', (data: any) => {
        const message: WebSocketMessage = {
          type: 'terminal_output',
          data,
          timestamp: new Date(),
        }
        setLastMessage(message)
      })

      newSocket.on('error', (error: any) => {
        console.error('WebSocket error:', error)
        const message: WebSocketMessage = {
          type: 'error',
          data: error,
          timestamp: new Date(),
        }
        setLastMessage(message)
      })

      setSocket(newSocket)
    }

    connectSocket()

    return () => {
      if (socket) {
        socket.disconnect()
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])

  const sendMessage = (message: any) => {
    if (socket && isConnected) {
      socket.emit('message', message)
    } else {
      console.warn('Socket not connected, cannot send message')
    }
  }

  return (
    <WebSocketContext.Provider value={{
      socket,
      isConnected,
      sendMessage,
      lastMessage,
    }}>
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWebSocket() {
  const context = useContext(WebSocketContext)
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}