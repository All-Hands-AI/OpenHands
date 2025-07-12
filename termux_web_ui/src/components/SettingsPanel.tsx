import React, { useState } from 'react'
import { Save, TestTube, RotateCcw, Eye, EyeOff, Check, X, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

import { useConfig } from '../hooks/useConfig'
import { DEFAULT_PROVIDERS, LLMProvider } from '../types'
import { configApi } from '../services/api'

function SettingsPanel() {
  const { config, updateConfig, resetConfig } = useConfig()
  const [showApiKey, setShowApiKey] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null)
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider | null>(
    DEFAULT_PROVIDERS.find(p => p.baseUrl === config.baseUrl) || null
  )

  const handleProviderChange = (provider: LLMProvider) => {
    setSelectedProvider(provider)
    updateConfig({
      baseUrl: provider.baseUrl,
      model: provider.models[0],
    })
    
    // Clear API key if provider doesn't require it
    if (!provider.requiresApiKey) {
      updateConfig({ apiKey: '' })
    }
  }

  const handleTestConnection = async () => {
    if (!config.apiKey && selectedProvider?.requiresApiKey) {
      toast.error('API key is required for this provider')
      return
    }

    setIsTesting(true)
    setTestResult(null)

    try {
      const result = await configApi.testConnection(config)
      
      if (result.success) {
        setTestResult('success')
        toast.success('Connection test successful!')
      } else {
        setTestResult('error')
        toast.error(result.error || 'Connection test failed')
      }
    } catch (error: any) {
      setTestResult('error')
      toast.error(error.message || 'Connection test failed')
    } finally {
      setIsTesting(false)
      
      // Clear test result after 3 seconds
      setTimeout(() => setTestResult(null), 3000)
    }
  }

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all settings to default?')) {
      resetConfig()
      setSelectedProvider(DEFAULT_PROVIDERS[0])
      toast.success('Settings reset to default')
    }
  }

  const handleSave = () => {
    toast.success('Settings saved successfully!')
  }

  return (
    <div className="h-full overflow-y-auto p-4 scrollbar-thin">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gradient mb-2">Settings</h1>
          <p className="text-dark-400">Configure your OpenHands Termux experience</p>
        </div>

        {/* LLM Provider */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">LLM Provider</h2>
            <p className="text-sm text-dark-400">Choose your AI model provider</p>
          </div>

          <div className="space-y-4">
            {/* Provider Selection */}
            <div>
              <label className="block text-sm font-medium mb-2">Provider</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {DEFAULT_PROVIDERS.map((provider) => (
                  <button
                    key={provider.name}
                    onClick={() => handleProviderChange(provider)}
                    className={`p-3 rounded-lg border text-left transition-colors ${
                      selectedProvider?.name === provider.name
                        ? 'border-primary-500 bg-primary-900/20 text-primary-200'
                        : 'border-dark-600 bg-dark-800 hover:border-dark-500'
                    }`}
                  >
                    <div className="font-medium">{provider.name}</div>
                    <div className="text-xs text-dark-400 mt-1">
                      {provider.models.length} models available
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Base URL */}
            <div>
              <label className="block text-sm font-medium mb-2">Base URL</label>
              <input
                type="url"
                value={config.baseUrl}
                onChange={(e) => updateConfig({ baseUrl: e.target.value })}
                className="input"
                placeholder="https://api.openai.com/v1"
              />
            </div>

            {/* API Key */}
            {selectedProvider?.requiresApiKey && (
              <div>
                <label className="block text-sm font-medium mb-2">API Key</label>
                <div className="relative">
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    value={config.apiKey}
                    onChange={(e) => updateConfig({ apiKey: e.target.value })}
                    className="input pr-10"
                    placeholder="Enter your API key"
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-dark-400 hover:text-dark-200"
                  >
                    {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            )}

            {/* Model */}
            <div>
              <label className="block text-sm font-medium mb-2">Model</label>
              <select
                value={config.model}
                onChange={(e) => updateConfig({ model: e.target.value })}
                className="input"
              >
                {selectedProvider?.models.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>

            {/* Test Connection */}
            <div className="flex items-center space-x-3">
              <button
                onClick={handleTestConnection}
                disabled={isTesting || (!config.apiKey && selectedProvider?.requiresApiKey)}
                className="btn btn-secondary flex items-center space-x-2"
              >
                {isTesting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <TestTube className="w-4 h-4" />
                )}
                <span>Test Connection</span>
              </button>

              {testResult && (
                <div className={`flex items-center space-x-1 ${
                  testResult === 'success' ? 'text-green-400' : 'text-red-400'
                }`}>
                  {testResult === 'success' ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <X className="w-4 h-4" />
                  )}
                  <span className="text-sm">
                    {testResult === 'success' ? 'Connected' : 'Failed'}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Model Parameters */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">Model Parameters</h2>
            <p className="text-sm text-dark-400">Fine-tune model behavior</p>
          </div>

          <div className="space-y-4">
            {/* Temperature */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Temperature: {config.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={config.temperature}
                onChange={(e) => updateConfig({ temperature: parseFloat(e.target.value) })}
                className="w-full h-2 bg-dark-700 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-xs text-dark-400 mt-1">
                <span>Focused (0.0)</span>
                <span>Balanced (1.0)</span>
                <span>Creative (2.0)</span>
              </div>
            </div>

            {/* Max Tokens */}
            <div>
              <label className="block text-sm font-medium mb-2">Max Tokens</label>
              <input
                type="number"
                min="1"
                max="8192"
                value={config.maxTokens}
                onChange={(e) => updateConfig({ maxTokens: parseInt(e.target.value) })}
                className="input"
              />
              <p className="text-xs text-dark-400 mt-1">
                Maximum number of tokens in the response
              </p>
            </div>
          </div>
        </div>

        {/* System Prompt */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">System Prompt</h2>
            <p className="text-sm text-dark-400">Customize the AI's behavior and personality</p>
          </div>

          <div>
            <textarea
              value={config.systemPrompt}
              onChange={(e) => updateConfig({ systemPrompt: e.target.value })}
              className="textarea h-32"
              placeholder="Enter system prompt..."
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleSave}
            className="btn btn-primary flex items-center justify-center space-x-2"
          >
            <Save className="w-4 h-4" />
            <span>Save Settings</span>
          </button>

          <button
            onClick={handleReset}
            className="btn btn-secondary flex items-center justify-center space-x-2"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Reset to Default</span>
          </button>
        </div>

        {/* Info */}
        <div className="card bg-blue-900/20 border-blue-700/50">
          <div className="flex items-start space-x-3">
            <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              <span className="text-white text-xs font-bold">i</span>
            </div>
            <div className="text-sm text-blue-200">
              <p className="font-medium mb-1">Configuration Tips:</p>
              <ul className="space-y-1 text-blue-300">
                <li>• Use lower temperature (0.0-0.3) for factual, consistent responses</li>
                <li>• Use higher temperature (0.7-1.0) for creative, varied responses</li>
                <li>• Adjust max tokens based on your needs (longer responses = more tokens)</li>
                <li>• Test your connection after changing provider or API key</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPanel