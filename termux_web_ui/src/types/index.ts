export interface Config {
  apiKey: string
  baseUrl: string
  model: string
  temperature: number
  maxTokens: number
  systemPrompt: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'error'
  content: string
  timestamp: Date
  isLoading?: boolean
}

export interface SystemInfo {
  cpu: {
    count: number
    percent: number
  }
  memory: {
    total: number
    used: number
    available: number
    percent: number
  }
  disk: {
    total: number
    used: number
    free: number
    percent: number
  }
  battery?: {
    percentage: number
    status: string
  }
  network?: {
    bytes_sent: number
    bytes_recv: number
  }
}

export interface TerminalSession {
  id: string
  command: string
  output: string
  exitCode: number
  timestamp: Date
  isRunning: boolean
}

export interface WebSocketMessage {
  type: 'message' | 'system_info' | 'terminal_output' | 'error'
  data: any
  timestamp: Date
}

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface LLMProvider {
  name: string
  baseUrl: string
  models: string[]
  requiresApiKey: boolean
}

export const DEFAULT_PROVIDERS: LLMProvider[] = [
  {
    name: 'LLM7 (Default)',
    baseUrl: 'https://api.llm7.io/v1',
    models: ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'claude-3-sonnet', 'claude-3-haiku'],
    requiresApiKey: false,
  },
  {
    name: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1',
    models: ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4o'],
    requiresApiKey: true,
  },
  {
    name: 'Anthropic',
    baseUrl: 'https://api.anthropic.com',
    models: ['claude-3-sonnet-20240229', 'claude-3-haiku-20240307', 'claude-3-opus-20240229'],
    requiresApiKey: true,
  },
  {
    name: 'Google Gemini',
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta',
    models: ['gemini-pro', 'gemini-pro-vision'],
    requiresApiKey: true,
  },
  {
    name: 'Groq',
    baseUrl: 'https://api.groq.com/openai/v1',
    models: ['mixtral-8x7b-32768', 'llama2-70b-4096', 'gemma-7b-it'],
    requiresApiKey: true,
  },
  {
    name: 'Ollama (Local)',
    baseUrl: 'http://localhost:11434/v1',
    models: ['llama2', 'codellama', 'mistral', 'neural-chat'],
    requiresApiKey: false,
  },
]