import React, { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, AlertCircle, Loader2, Copy, Check } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import toast from 'react-hot-toast'

import { Message } from '../types'
import { useConfig } from '../hooks/useConfig'
import { chatApi } from '../services/api'

function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const { config, isConfigured } = useConfig()

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Add welcome message
  useEffect(() => {
    if (messages.length === 0) {
      const welcomeMessage: Message = {
        id: 'welcome',
        role: 'system',
        content: `🚀 **Welcome to OpenHands Termux!**

I'm your AI assistant running on Android. I can help you with:

- **Programming & Development**: Write, debug, and explain code
- **System Administration**: Manage files, run commands, monitor system
- **Data Analysis**: Analyze CSV files, create visualizations
- **Web Scraping**: Extract data from websites
- **Automation**: Create scripts and workflows
- **General Questions**: Answer any questions you have

${!isConfigured ? '⚠️ **Please configure your API settings first** in the Settings tab.' : '✅ **Ready to chat!** What would you like to work on?'}`,
        timestamp: new Date(),
      }
      setMessages([welcomeMessage])
    }
  }, [isConfigured])

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    if (!isConfigured) {
      toast.error('Please configure your API settings first')
      return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    }

    setMessages(prev => [...prev, userMessage, loadingMessage])
    setInput('')
    setIsLoading(true)

    try {
      let assistantContent = ''
      
      // Use streaming if available
      const result = await chatApi.streamMessage(
        input.trim(),
        config,
        (chunk: string) => {
          assistantContent += chunk
          setMessages(prev => 
            prev.map(msg => 
              msg.id === loadingMessage.id 
                ? { ...msg, content: assistantContent, isLoading: false }
                : msg
            )
          )
        }
      )

      if (!result.success) {
        // Fallback to regular API
        const fallbackResult = await chatApi.sendMessage(input.trim(), config)
        
        if (fallbackResult.success && fallbackResult.data) {
          setMessages(prev => 
            prev.map(msg => 
              msg.id === loadingMessage.id 
                ? { ...msg, content: fallbackResult.data!, isLoading: false }
                : msg
            )
          )
        } else {
          throw new Error(fallbackResult.error || 'Failed to get response')
        }
      }
    } catch (error: any) {
      console.error('Chat error:', error)
      
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        role: 'error',
        content: `❌ **Error**: ${error.message || 'Failed to send message'}\n\nPlease check your API configuration and try again.`,
        timestamp: new Date(),
      }

      setMessages(prev => 
        prev.filter(msg => msg.id !== loadingMessage.id).concat(errorMessage)
      )
      
      toast.error(error.message || 'Failed to send message')
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const copyToClipboard = async (content: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(content)
      setCopiedId(messageId)
      toast.success('Copied to clipboard')
      setTimeout(() => setCopiedId(null), 2000)
    } catch (error) {
      toast.error('Failed to copy')
    }
  }

  const clearChat = () => {
    setMessages([])
    toast.success('Chat cleared')
  }

  const renderMessage = (message: Message) => {
    const isUser = message.role === 'user'
    const isSystem = message.role === 'system'
    const isError = message.role === 'error'

    return (
      <div
        key={message.id}
        className={`message ${
          isUser ? 'message-user' : 
          isError ? 'message-error' : 
          isSystem ? 'message-system' : 
          'message-assistant'
        }`}
      >
        <div className="flex items-start space-x-3">
          {/* Avatar */}
          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            isUser ? 'bg-primary-600' : 
            isError ? 'bg-red-600' : 
            isSystem ? 'bg-yellow-600' : 
            'bg-dark-600'
          }`}>
            {isUser ? (
              <User className="w-4 h-4 text-white" />
            ) : isError ? (
              <AlertCircle className="w-4 h-4 text-white" />
            ) : (
              <Bot className="w-4 h-4 text-white" />
            )}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-dark-300">
                {isUser ? 'You' : isError ? 'Error' : isSystem ? 'System' : 'OpenHands'}
              </span>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-dark-500">
                  {message.timestamp.toLocaleTimeString()}
                </span>
                {!isUser && (
                  <button
                    onClick={() => copyToClipboard(message.content, message.id)}
                    className="p-1 text-dark-400 hover:text-dark-200 transition-colors"
                    title="Copy message"
                  >
                    {copiedId === message.id ? (
                      <Check className="w-3 h-3" />
                    ) : (
                      <Copy className="w-3 h-3" />
                    )}
                  </button>
                )}
              </div>
            </div>

            <div className="prose prose-invert prose-sm max-w-none">
              {message.isLoading ? (
                <div className="flex items-center space-x-2 text-dark-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Thinking...</span>
                </div>
              ) : (
                <ReactMarkdown
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '')
                      return !inline && match ? (
                        <div className="code-block">
                          <div className="code-header">
                            <span>{match[1]}</span>
                            <button
                              onClick={() => copyToClipboard(String(children), `${message.id}-code`)}
                              className="text-dark-400 hover:text-dark-200 transition-colors"
                            >
                              {copiedId === `${message.id}-code` ? (
                                <Check className="w-3 h-3" />
                              ) : (
                                <Copy className="w-3 h-3" />
                              )}
                            </button>
                          </div>
                          <SyntaxHighlighter
                            style={oneDark}
                            language={match[1]}
                            PreTag="div"
                            className="code-content"
                            {...props}
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        </div>
                      ) : (
                        <code className="bg-dark-700 px-1 py-0.5 rounded text-sm" {...props}>
                          {children}
                        </code>
                      )
                    },
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!isConfigured) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6 text-center">
        <AlertCircle className="w-16 h-16 text-yellow-500 mb-4" />
        <h2 className="text-xl font-semibold mb-2">Configuration Required</h2>
        <p className="text-dark-400 mb-4">
          Please configure your API settings in the Settings tab to start chatting.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
        {messages.map(renderMessage)}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-dark-700 p-4">
        <div className="flex items-end space-x-3">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
              className="textarea resize-none min-h-[44px] max-h-32"
              rows={1}
              disabled={isLoading}
            />
          </div>
          
          <div className="flex space-x-2">
            {messages.length > 1 && (
              <button
                onClick={clearChat}
                className="btn btn-ghost"
                disabled={isLoading}
              >
                Clear
              </button>
            )}
            
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="btn btn-primary"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface