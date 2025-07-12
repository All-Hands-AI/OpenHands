import { useContext } from 'react'
import { WebSocketContext } from '../contexts/WebSocketContext'

export function useWebSocket() {
  const context = useContext(WebSocketContext)
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}