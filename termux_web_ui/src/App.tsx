import React, { useState, useEffect } from 'react'
import { Toaster } from 'react-hot-toast'
import { Settings, MessageCircle, Terminal, BarChart3, Wifi, WifiOff, Folder, GitBranch } from 'lucide-react'

import ChatInterface from './components/ChatInterface'
import SettingsPanel from './components/SettingsPanel'
import SystemMonitor from './components/SystemMonitor'
import TerminalPanel from './components/TerminalPanel'
import FileBrowser from './components/FileBrowser'
import GitPanel from './components/GitPanel'
import { ConfigProvider } from './contexts/ConfigContext'
import { WebSocketProvider } from './contexts/WebSocketContext'
import { useConfig } from './hooks/useConfig'
import { useWebSocket } from './hooks/useWebSocket'

type Tab = 'chat' | 'settings' | 'monitor' | 'terminal' | 'files' | 'git'

function AppContent() {
  const [activeTab, setActiveTab] = useState<Tab>('chat')
  const [isMobile, setIsMobile] = useState(false)
  const { config } = useConfig()
  const { isConnected } = useWebSocket()

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const tabs = [
    { id: 'chat' as Tab, label: 'Chat', icon: MessageCircle },
    { id: 'files' as Tab, label: 'Files', icon: Folder },
    { id: 'git' as Tab, label: 'Git', icon: GitBranch },
    { id: 'terminal' as Tab, label: 'Terminal', icon: Terminal },
    { id: 'monitor' as Tab, label: 'Monitor', icon: BarChart3 },
    { id: 'settings' as Tab, label: 'Settings', icon: Settings },
  ]

  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatInterface />
      case 'files':
        return <FileBrowser />
      case 'git':
        return <GitPanel />
      case 'settings':
        return <SettingsPanel />
      case 'monitor':
        return <SystemMonitor />
      case 'terminal':
        return <TerminalPanel />
      default:
        return <ChatInterface />
    }
  }

  return (
    <div className="flex flex-col h-screen bg-dark-900 text-dark-50">
      {/* Header */}
      <header className="flex items-center justify-between p-4 border-b border-dark-700 bg-dark-800">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">OH</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gradient">OpenHands</h1>
            <p className="text-xs text-dark-400">Termux Edition</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Connection Status */}
          <div className="flex items-center space-x-1">
            {isConnected ? (
              <Wifi className="w-4 h-4 text-green-500" />
            ) : (
              <WifiOff className="w-4 h-4 text-red-500" />
            )}
            <span className="text-xs text-dark-400 hidden sm:inline">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          
          {/* API Status */}
          {config.apiKey && (
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        {renderContent()}
      </main>

      {/* Bottom Navigation */}
      <nav className="border-t border-dark-700 bg-dark-800">
        <div className="flex overflow-x-auto scrollbar-thin">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-shrink-0 flex flex-col items-center justify-center py-2 px-3 min-w-[60px] transition-colors relative ${
                  isActive
                    ? 'text-primary-400 bg-primary-900/20'
                    : 'text-dark-400 hover:text-dark-200 hover:bg-dark-700'
                }`}
              >
                <Icon className="w-4 h-4 mb-1" />
                <span className="text-xs font-medium truncate">{tab.label}</span>
                {isActive && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500"></div>
                )}
              </button>
            )
          })}
        </div>
      </nav>

      {/* Toast Notifications */}
      <Toaster
        position="top-center"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid #475569',
            borderRadius: '8px',
            fontSize: '14px',
          },
          success: {
            iconTheme: {
              primary: '#10b981',
              secondary: '#f1f5f9',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#f1f5f9',
            },
          },
        }}
      />
    </div>
  )
}

function App() {
  return (
    <ConfigProvider>
      <WebSocketProvider>
        <AppContent />
      </WebSocketProvider>
    </ConfigProvider>
  )
}

export default App