import React, { useState, useEffect } from 'react'
import { RefreshCw, Cpu, HardDrive, Zap, Wifi, Smartphone } from 'lucide-react'
import toast from 'react-hot-toast'

import { SystemInfo } from '../types'
import { systemApi } from '../services/api'

function SystemMonitor() {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null)

  const fetchSystemInfo = async () => {
    setIsLoading(true)
    try {
      const result = await systemApi.getSystemInfo()
      if (result.success && result.data) {
        setSystemInfo(result.data)
      } else {
        toast.error(result.error || 'Failed to fetch system info')
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to fetch system info')
    } finally {
      setIsLoading(false)
    }
  }

  const toggleAutoRefresh = () => {
    if (autoRefresh) {
      if (refreshInterval) {
        clearInterval(refreshInterval)
        setRefreshInterval(null)
      }
      setAutoRefresh(false)
      toast.success('Auto-refresh disabled')
    } else {
      const interval = setInterval(fetchSystemInfo, 5000) // Refresh every 5 seconds
      setRefreshInterval(interval)
      setAutoRefresh(true)
      toast.success('Auto-refresh enabled (5s)')
    }
  }

  useEffect(() => {
    fetchSystemInfo()
    
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    }
  }, [])

  const formatBytes = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    let size = bytes
    let unitIndex = 0
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024
      unitIndex++
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`
  }

  const getUsageColor = (percent: number): string => {
    if (percent < 50) return 'bg-green-500'
    if (percent < 80) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const ProgressBar = ({ 
    value, 
    max, 
    label, 
    color 
  }: { 
    value: number
    max: number
    label: string
    color?: string 
  }) => {
    const percentage = (value / max) * 100
    const barColor = color || getUsageColor(percentage)
    
    return (
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-dark-300">{label}</span>
          <span className="text-dark-400">{percentage.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-dark-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${barColor}`}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-dark-400">
          <span>{formatBytes(value)}</span>
          <span>{formatBytes(max)}</span>
        </div>
      </div>
    )
  }

  const StatCard = ({ 
    icon: Icon, 
    title, 
    children 
  }: { 
    icon: React.ElementType
    title: string
    children: React.ReactNode 
  }) => (
    <div className="card">
      <div className="flex items-center space-x-3 mb-4">
        <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
          <Icon className="w-5 h-5 text-white" />
        </div>
        <h3 className="text-lg font-semibold">{title}</h3>
      </div>
      {children}
    </div>
  )

  if (!systemInfo && !isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6 text-center">
        <Smartphone className="w-16 h-16 text-dark-500 mb-4" />
        <h2 className="text-xl font-semibold mb-2">System Monitor</h2>
        <p className="text-dark-400 mb-4">
          Monitor your Termux system performance and resources
        </p>
        <button
          onClick={fetchSystemInfo}
          className="btn btn-primary"
        >
          Load System Info
        </button>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-4 scrollbar-thin">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gradient">System Monitor</h1>
            <p className="text-dark-400">Real-time system performance</p>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={toggleAutoRefresh}
              className={`btn ${autoRefresh ? 'btn-primary' : 'btn-secondary'}`}
            >
              {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
            </button>
            
            <button
              onClick={fetchSystemInfo}
              disabled={isLoading}
              className="btn btn-ghost"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {isLoading && !systemInfo ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin text-primary-500" />
          </div>
        ) : systemInfo ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* CPU */}
            <StatCard icon={Cpu} title="CPU">
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-dark-300">Cores</span>
                  <span className="font-mono">{systemInfo.cpu.count}</span>
                </div>
                <ProgressBar
                  value={systemInfo.cpu.percent}
                  max={100}
                  label="Usage"
                  color={getUsageColor(systemInfo.cpu.percent)}
                />
              </div>
            </StatCard>

            {/* Memory */}
            <StatCard icon={HardDrive} title="Memory">
              <ProgressBar
                value={systemInfo.memory.used}
                max={systemInfo.memory.total}
                label="RAM Usage"
              />
            </StatCard>

            {/* Storage */}
            <StatCard icon={HardDrive} title="Storage">
              <ProgressBar
                value={systemInfo.disk.used}
                max={systemInfo.disk.total}
                label="Disk Usage"
              />
            </StatCard>

            {/* Battery */}
            {systemInfo.battery && (
              <StatCard icon={Zap} title="Battery">
                <div className="space-y-4">
                  <ProgressBar
                    value={systemInfo.battery.percentage}
                    max={100}
                    label="Battery Level"
                    color={systemInfo.battery.percentage > 20 ? 'bg-green-500' : 'bg-red-500'}
                  />
                  <div className="flex justify-between">
                    <span className="text-dark-300">Status</span>
                    <span className={`font-mono ${
                      systemInfo.battery.status === 'Charging' ? 'text-green-400' : 'text-dark-400'
                    }`}>
                      {systemInfo.battery.status}
                    </span>
                  </div>
                </div>
              </StatCard>
            )}

            {/* Network */}
            {systemInfo.network && (
              <StatCard icon={Wifi} title="Network">
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-dark-300">Sent</span>
                    <span className="font-mono text-green-400">
                      {formatBytes(systemInfo.network.bytes_sent)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-300">Received</span>
                    <span className="font-mono text-blue-400">
                      {formatBytes(systemInfo.network.bytes_recv)}
                    </span>
                  </div>
                </div>
              </StatCard>
            )}

            {/* System Details */}
            <div className="lg:col-span-2">
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">System Details</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-dark-300">Total Memory</span>
                      <span className="font-mono">{formatBytes(systemInfo.memory.total)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-300">Available Memory</span>
                      <span className="font-mono">{formatBytes(systemInfo.memory.available)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-300">Free Memory</span>
                      <span className="font-mono">{formatBytes(systemInfo.memory.free)}</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-dark-300">Total Storage</span>
                      <span className="font-mono">{formatBytes(systemInfo.disk.total)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-300">Used Storage</span>
                      <span className="font-mono">{formatBytes(systemInfo.disk.used)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-dark-300">Free Storage</span>
                      <span className="font-mono">{formatBytes(systemInfo.disk.free)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-dark-400">Failed to load system information</p>
          </div>
        )}

        {/* Last Updated */}
        {systemInfo && (
          <div className="text-center text-xs text-dark-500">
            Last updated: {new Date().toLocaleString()}
          </div>
        )}
      </div>
    </div>
  )
}

export default SystemMonitor