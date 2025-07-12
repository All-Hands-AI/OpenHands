import axios from 'axios'
import { Config, ApiResponse, SystemInfo, Message } from '../types'

// Create axios instance
const api = axios.create({
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// API base URL - try local backend first, fallback to mock
const getBaseUrl = () => {
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:8000/api'
  }
  return '/api'
}

api.defaults.baseURL = getBaseUrl()

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Error:', error)
    
    // Handle network errors
    if (!error.response) {
      return Promise.reject({
        message: 'Network error. Please check your connection.',
        status: 0,
      })
    }
    
    // Handle HTTP errors
    const { status, data } = error.response
    return Promise.reject({
      message: data?.message || `HTTP ${status} Error`,
      status,
      data,
    })
  }
)

// Chat API
export const chatApi = {
  sendMessage: async (message: string, config: Config): Promise<ApiResponse<string>> => {
    try {
      const response = await api.post('/chat', {
        message,
        config: {
          model: config.model,
          temperature: config.temperature,
          max_tokens: config.maxTokens,
          system_prompt: config.systemPrompt,
        },
        api_key: config.apiKey,
        base_url: config.baseUrl,
      })
      
      return {
        success: true,
        data: response.data.response,
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to send message',
      }
    }
  },

  streamMessage: async (
    message: string, 
    config: Config, 
    onChunk: (chunk: string) => void
  ): Promise<ApiResponse> => {
    try {
      const response = await fetch(`${getBaseUrl()}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          config: {
            model: config.model,
            temperature: config.temperature,
            max_tokens: config.maxTokens,
            system_prompt: config.systemPrompt,
          },
          api_key: config.apiKey,
          base_url: config.baseUrl,
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              return { success: true }
            }
            try {
              const parsed = JSON.parse(data)
              if (parsed.content) {
                onChunk(parsed.content)
              }
            } catch (e) {
              // Ignore parsing errors for individual chunks
            }
          }
        }
      }

      return { success: true }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to stream message',
      }
    }
  },
}

// System API
export const systemApi = {
  getSystemInfo: async (): Promise<ApiResponse<SystemInfo>> => {
    try {
      const response = await api.get('/system/info')
      return {
        success: true,
        data: response.data,
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to get system info',
      }
    }
  },

  executeCommand: async (command: string): Promise<ApiResponse<{
    stdout: string
    stderr: string
    exitCode: number
  }>> => {
    try {
      const response = await api.post('/system/execute', { command })
      return {
        success: true,
        data: response.data,
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to execute command',
      }
    }
  },
}

// File API
export const fileApi = {
  readFile: async (path: string): Promise<ApiResponse<string>> => {
    try {
      const response = await api.get(`/files/read?path=${encodeURIComponent(path)}`)
      return {
        success: true,
        data: response.data.content,
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to read file',
      }
    }
  },

  writeFile: async (path: string, content: string): Promise<ApiResponse> => {
    try {
      await api.post('/files/write', { path, content })
      return { success: true }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to write file',
      }
    }
  },

  listDirectory: async (path: string): Promise<ApiResponse<Array<{
    name: string
    type: 'file' | 'directory'
    size: number
  }>>> => {
    try {
      const response = await api.get(`/files/list?path=${encodeURIComponent(path)}`)
      return {
        success: true,
        data: response.data.files,
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to list directory',
      }
    }
  },
}

// Config API
export const configApi = {
  testConnection: async (config: Config): Promise<ApiResponse> => {
    try {
      const response = await api.post('/config/test', {
        api_key: config.apiKey,
        base_url: config.baseUrl,
        model: config.model,
      })
      return {
        success: true,
        data: response.data,
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Connection test failed',
      }
    }
  },

  getModels: async (baseUrl: string, apiKey?: string): Promise<ApiResponse<string[]>> => {
    try {
      const response = await api.post('/config/models', {
        base_url: baseUrl,
        api_key: apiKey,
      })
      return {
        success: true,
        data: response.data.models,
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to get models',
      }
    }
  },
}

export default api