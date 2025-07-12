import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { Config } from '../types'

interface ConfigContextType {
  config: Config
  updateConfig: (updates: Partial<Config>) => void
  resetConfig: () => void
  isConfigured: boolean
}

const defaultConfig: Config = {
  apiKey: 'unused',
  baseUrl: 'https://api.llm7.io/v1',
  model: 'gpt-3.5-turbo',
  temperature: 0.7,
  maxTokens: 2048,
  systemPrompt: `You are OpenHands AI Assistant running in Termux on Android.

You can help with:
- Answering questions
- Writing and explaining code
- Helping with programming tasks
- Providing solutions and advice
- File operations and system tasks
- Git operations and version control
- GitHub integration and repository management
- System administration and monitoring
- Data analysis and visualization
- Web scraping and automation

You have access to various tools for file operations, command execution, and system interaction.
Provide clear and practical answers optimized for the Termux/Android environment.`,
}

const ConfigContext = createContext<ConfigContextType | undefined>(undefined)

export function ConfigProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<Config>(defaultConfig)

  // Load config from localStorage on mount
  useEffect(() => {
    const savedConfig = localStorage.getItem('openhands-termux-config')
    if (savedConfig) {
      try {
        const parsed = JSON.parse(savedConfig)
        setConfig({ ...defaultConfig, ...parsed })
      } catch (error) {
        console.error('Failed to parse saved config:', error)
      }
    }
  }, [])

  // Save config to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('openhands-termux-config', JSON.stringify(config))
  }, [config])

  const updateConfig = (updates: Partial<Config>) => {
    setConfig(prev => ({ ...prev, ...updates }))
  }

  const resetConfig = () => {
    setConfig(defaultConfig)
    localStorage.removeItem('openhands-termux-config')
  }

  const isConfigured = Boolean(config.apiKey && config.baseUrl && config.model)

  return (
    <ConfigContext.Provider value={{
      config,
      updateConfig,
      resetConfig,
      isConfigured,
    }}>
      {children}
    </ConfigContext.Provider>
  )
}

export function useConfig() {
  const context = useContext(ConfigContext)
  if (context === undefined) {
    throw new Error('useConfig must be used within a ConfigProvider')
  }
  return context
}