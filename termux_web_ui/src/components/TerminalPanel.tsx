import React, { useState, useEffect, useRef } from 'react'
import { Terminal, Play, Square, Trash2, Copy, Download } from 'lucide-react'
import toast from 'react-hot-toast'

import { TerminalSession } from '../types'
import { systemApi } from '../services/api'

function TerminalPanel() {
  const [sessions, setSessions] = useState<TerminalSession[]>([])
  const [currentCommand, setCurrentCommand] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [history, setHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const terminalRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [sessions])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Load command history from localStorage
  useEffect(() => {
    const savedHistory = localStorage.getItem('termux-command-history')
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory))
      } catch (error) {
        console.error('Failed to load command history:', error)
      }
    }
  }, [])

  // Save command history to localStorage
  useEffect(() => {
    localStorage.setItem('termux-command-history', JSON.stringify(history))
  }, [history])

  const executeCommand = async (command: string) => {
    if (!command.trim() || isRunning) return

    const session: TerminalSession = {
      id: Date.now().toString(),
      command: command.trim(),
      output: '',
      exitCode: 0,
      timestamp: new Date(),
      isRunning: true,
    }

    setSessions(prev => [...prev, session])
    setCurrentCommand('')
    setIsRunning(true)

    // Add to history
    const newHistory = [command.trim(), ...history.filter(h => h !== command.trim())].slice(0, 100)
    setHistory(newHistory)
    setHistoryIndex(-1)

    try {
      const result = await systemApi.executeCommand(command.trim())
      
      if (result.success && result.data) {
        setSessions(prev => 
          prev.map(s => 
            s.id === session.id 
              ? {
                  ...s,
                  output: result.data!.stdout + (result.data!.stderr ? '\n' + result.data!.stderr : ''),
                  exitCode: result.data!.exitCode,
                  isRunning: false,
                }
              : s
          )
        )
      } else {
        setSessions(prev => 
          prev.map(s => 
            s.id === session.id 
              ? {
                  ...s,
                  output: result.error || 'Command execution failed',
                  exitCode: 1,
                  isRunning: false,
                }
              : s
          )
        )
      }
    } catch (error: any) {
      setSessions(prev => 
        prev.map(s => 
          s.id === session.id 
            ? {
                ...s,
                output: error.message || 'Command execution failed',
                exitCode: 1,
                isRunning: false,
              }
            : s
        )
      )
    } finally {
      setIsRunning(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      executeCommand(currentCommand)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (historyIndex < history.length - 1) {
        const newIndex = historyIndex + 1
        setHistoryIndex(newIndex)
        setCurrentCommand(history[newIndex] || '')
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1
        setHistoryIndex(newIndex)
        setCurrentCommand(history[newIndex] || '')
      } else if (historyIndex === 0) {
        setHistoryIndex(-1)
        setCurrentCommand('')
      }
    }
  }

  const clearTerminal = () => {
    setSessions([])
    toast.success('Terminal cleared')
  }

  const copyOutput = (output: string) => {
    navigator.clipboard.writeText(output)
    toast.success('Output copied to clipboard')
  }

  const downloadSession = (session: TerminalSession) => {
    const content = `Command: ${session.command}\nTimestamp: ${session.timestamp.toISOString()}\nExit Code: ${session.exitCode}\n\nOutput:\n${session.output}`
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `terminal-session-${session.id}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    toast.success('Session downloaded')
  }

  const commonCommands = [
    'ls -la',
    'pwd',
    'whoami',
    'uname -a',
    'df -h',
    'free -h',
    'ps aux',
    'top',
    'pkg list-installed',
    'termux-info',
  ]

  return (
    <div className="flex flex-col h-full bg-dark-900">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-dark-700 bg-dark-800">
        <div className="flex items-center space-x-3">
          <Terminal className="w-5 h-5 text-primary-400" />
          <h2 className="text-lg font-semibold">Terminal</h2>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={clearTerminal}
            className="btn btn-ghost btn-sm"
            disabled={isRunning}
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Terminal Output */}
      <div 
        ref={terminalRef}
        className="flex-1 overflow-y-auto p-4 font-mono text-sm bg-black scrollbar-thin"
      >
        {sessions.length === 0 ? (
          <div className="text-green-400">
            <div className="mb-4">
              Welcome to OpenHands Termux Terminal
            </div>
            <div className="text-dark-400 text-xs mb-4">
              Type commands below or click on common commands to get started.
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mb-4">
              {commonCommands.map((cmd) => (
                <button
                  key={cmd}
                  onClick={() => setCurrentCommand(cmd)}
                  className="text-left text-xs p-2 bg-dark-800 hover:bg-dark-700 rounded border border-dark-600 text-blue-400 hover:text-blue-300 transition-colors"
                >
                  {cmd}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {sessions.map((session) => (
              <div key={session.id} className="space-y-2">
                {/* Command */}
                <div className="flex items-center space-x-2">
                  <span className="text-green-400">$</span>
                  <span className="text-white">{session.command}</span>
                  <span className="text-dark-500 text-xs">
                    {session.timestamp.toLocaleTimeString()}
                  </span>
                  {session.isRunning && (
                    <div className="flex items-center space-x-1 text-yellow-400">
                      <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
                      <span className="text-xs">Running...</span>
                    </div>
                  )}
                </div>

                {/* Output */}
                {session.output && (
                  <div className="relative group">
                    <pre className="text-gray-300 whitespace-pre-wrap break-words bg-dark-800 p-3 rounded border border-dark-600">
                      {session.output}
                    </pre>
                    
                    {/* Action buttons */}
                    <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex space-x-1">
                      <button
                        onClick={() => copyOutput(session.output)}
                        className="p-1 bg-dark-700 hover:bg-dark-600 rounded text-dark-300 hover:text-white transition-colors"
                        title="Copy output"
                      >
                        <Copy className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => downloadSession(session)}
                        className="p-1 bg-dark-700 hover:bg-dark-600 rounded text-dark-300 hover:text-white transition-colors"
                        title="Download session"
                      >
                        <Download className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                )}

                {/* Exit code */}
                {!session.isRunning && (
                  <div className="text-xs">
                    <span className="text-dark-500">Exit code: </span>
                    <span className={session.exitCode === 0 ? 'text-green-400' : 'text-red-400'}>
                      {session.exitCode}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-dark-700 p-4 bg-dark-800">
        <div className="flex items-center space-x-3">
          <span className="text-green-400 font-mono">$</span>
          <input
            ref={inputRef}
            type="text"
            value={currentCommand}
            onChange={(e) => setCurrentCommand(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Enter command..."
            className="flex-1 bg-transparent text-white font-mono focus:outline-none"
            disabled={isRunning}
          />
          <button
            onClick={() => executeCommand(currentCommand)}
            disabled={!currentCommand.trim() || isRunning}
            className="btn btn-primary btn-sm"
          >
            {isRunning ? (
              <Square className="w-4 h-4" />
            ) : (
              <Play className="w-4 h-4" />
            )}
          </button>
        </div>
        
        {/* Help text */}
        <div className="text-xs text-dark-500 mt-2">
          Press Enter to execute • Use ↑/↓ arrows for command history • Ctrl+C to interrupt
        </div>
      </div>
    </div>
  )
}

export default TerminalPanel