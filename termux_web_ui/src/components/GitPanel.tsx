import React, { useState, useEffect } from 'react'
import { 
  GitBranch, 
  GitCommit, 
  GitPullRequest, 
  Plus, 
  RefreshCw, 
  Upload, 
  Download,
  Settings,
  User,
  Key,
  Globe,
  CheckCircle,
  XCircle,
  Clock,
  FileText,
  Trash2
} from 'lucide-react'
import toast from 'react-hot-toast'

import { systemApi } from '../services/api'

interface GitStatus {
  branch: string
  ahead: number
  behind: number
  staged: string[]
  modified: string[]
  untracked: string[]
  clean: boolean
}

interface GitConfig {
  name: string
  email: string
  remoteUrl: string
}

function GitPanel() {
  const [gitStatus, setGitStatus] = useState<GitStatus | null>(null)
  const [gitConfig, setGitConfig] = useState<GitConfig>({ name: '', email: '', remoteUrl: '' })
  const [isLoading, setIsLoading] = useState(false)
  const [currentPath, setCurrentPath] = useState('/data/data/com.termux/files/home')
  const [commitMessage, setCommitMessage] = useState('')
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [branches, setBranches] = useState<string[]>([])
  const [remotes, setRemotes] = useState<string[]>([])

  const executeGitCommand = async (command: string): Promise<{ success: boolean; output: string; error?: string }> => {
    try {
      const result = await systemApi.executeCommand(`cd "${currentPath}" && ${command}`)
      if (result.success && result.data) {
        return {
          success: result.data.exitCode === 0,
          output: result.data.stdout,
          error: result.data.stderr
        }
      }
      return { success: false, output: '', error: result.error }
    } catch (error: any) {
      return { success: false, output: '', error: error.message }
    }
  }

  const checkGitRepo = async () => {
    const result = await executeGitCommand('git rev-parse --is-inside-work-tree')
    return result.success && result.output.trim() === 'true'
  }

  const loadGitStatus = async () => {
    setIsLoading(true)
    try {
      const isRepo = await checkGitRepo()
      if (!isRepo) {
        setGitStatus(null)
        return
      }

      // Get current branch
      const branchResult = await executeGitCommand('git branch --show-current')
      const branch = branchResult.success ? branchResult.output.trim() : 'main'

      // Get status
      const statusResult = await executeGitCommand('git status --porcelain')
      const statusLines = statusResult.success ? statusResult.output.split('\n').filter(line => line.trim()) : []

      const staged: string[] = []
      const modified: string[] = []
      const untracked: string[] = []

      statusLines.forEach(line => {
        const status = line.substring(0, 2)
        const file = line.substring(3)
        
        if (status[0] !== ' ' && status[0] !== '?') {
          staged.push(file)
        }
        if (status[1] === 'M') {
          modified.push(file)
        }
        if (status === '??') {
          untracked.push(file)
        }
      })

      // Get ahead/behind info
      const aheadBehindResult = await executeGitCommand(`git rev-list --left-right --count origin/${branch}...HEAD`)
      let ahead = 0, behind = 0
      if (aheadBehindResult.success) {
        const [behindStr, aheadStr] = aheadBehindResult.output.trim().split('\t')
        behind = parseInt(behindStr) || 0
        ahead = parseInt(aheadStr) || 0
      }

      setGitStatus({
        branch,
        ahead,
        behind,
        staged,
        modified,
        untracked,
        clean: statusLines.length === 0
      })

      // Load branches
      const branchesResult = await executeGitCommand('git branch -a')
      if (branchesResult.success) {
        const branchList = branchesResult.output
          .split('\n')
          .map(b => b.replace(/^\*?\s+/, '').replace(/^remotes\/origin\//, ''))
          .filter(b => b && !b.includes('HEAD'))
        setBranches([...new Set(branchList)])
      }

      // Load remotes
      const remotesResult = await executeGitCommand('git remote -v')
      if (remotesResult.success) {
        const remoteList = remotesResult.output
          .split('\n')
          .map(r => r.split('\t')[0])
          .filter(r => r)
        setRemotes([...new Set(remoteList)])
      }

    } catch (error: any) {
      toast.error(error.message || 'Failed to load git status')
    } finally {
      setIsLoading(false)
    }
  }

  const loadGitConfig = async () => {
    try {
      const nameResult = await executeGitCommand('git config user.name')
      const emailResult = await executeGitCommand('git config user.email')
      const remoteResult = await executeGitCommand('git config --get remote.origin.url')

      setGitConfig({
        name: nameResult.success ? nameResult.output.trim() : '',
        email: emailResult.success ? emailResult.output.trim() : '',
        remoteUrl: remoteResult.success ? remoteResult.output.trim() : ''
      })
    } catch (error: any) {
      console.error('Failed to load git config:', error)
    }
  }

  useEffect(() => {
    loadGitStatus()
    loadGitConfig()
  }, [currentPath])

  const initRepo = async () => {
    try {
      const result = await executeGitCommand('git init')
      if (result.success) {
        toast.success('Git repository initialized')
        loadGitStatus()
      } else {
        toast.error(result.error || 'Failed to initialize repository')
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to initialize repository')
    }
  }

  const addFiles = async (files: string[]) => {
    try {
      const fileList = files.map(f => `"${f}"`).join(' ')
      const result = await executeGitCommand(`git add ${fileList}`)
      if (result.success) {
        toast.success(`Added ${files.length} file(s)`)
        loadGitStatus()
      } else {
        toast.error(result.error || 'Failed to add files')
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to add files')
    }
  }

  const commitChanges = async () => {
    if (!commitMessage.trim()) {
      toast.error('Please enter a commit message')
      return
    }

    try {
      const result = await executeGitCommand(`git commit -m "${commitMessage}"`)
      if (result.success) {
        toast.success('Changes committed successfully')
        setCommitMessage('')
        loadGitStatus()
      } else {
        toast.error(result.error || 'Failed to commit changes')
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to commit changes')
    }
  }

  const pushChanges = async () => {
    try {
      const result = await executeGitCommand('git push origin HEAD')
      if (result.success) {
        toast.success('Changes pushed successfully')
        loadGitStatus()
      } else {
        toast.error(result.error || 'Failed to push changes')
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to push changes')
    }
  }

  const pullChanges = async () => {
    try {
      const result = await executeGitCommand('git pull origin HEAD')
      if (result.success) {
        toast.success('Changes pulled successfully')
        loadGitStatus()
      } else {
        toast.error(result.error || 'Failed to pull changes')
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to pull changes')
    }
  }

  const createBranch = async () => {
    const branchName = prompt('Enter new branch name:')
    if (!branchName) return

    try {
      const result = await executeGitCommand(`git checkout -b "${branchName}"`)
      if (result.success) {
        toast.success(`Created and switched to branch: ${branchName}`)
        loadGitStatus()
      } else {
        toast.error(result.error || 'Failed to create branch')
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to create branch')
    }
  }

  const switchBranch = async (branch: string) => {
    try {
      const result = await executeGitCommand(`git checkout "${branch}"`)
      if (result.success) {
        toast.success(`Switched to branch: ${branch}`)
        loadGitStatus()
      } else {
        toast.error(result.error || 'Failed to switch branch')
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to switch branch')
    }
  }

  const cloneRepo = async () => {
    const repoUrl = prompt('Enter repository URL:')
    if (!repoUrl) return

    try {
      const result = await executeGitCommand(`git clone "${repoUrl}"`)
      if (result.success) {
        toast.success('Repository cloned successfully')
        loadGitStatus()
      } else {
        toast.error(result.error || 'Failed to clone repository')
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to clone repository')
    }
  }

  const saveGitConfig = async () => {
    try {
      if (gitConfig.name) {
        await executeGitCommand(`git config user.name "${gitConfig.name}"`)
      }
      if (gitConfig.email) {
        await executeGitCommand(`git config user.email "${gitConfig.email}"`)
      }
      if (gitConfig.remoteUrl) {
        await executeGitCommand(`git remote set-url origin "${gitConfig.remoteUrl}"`)
      }
      
      toast.success('Git configuration saved')
      setShowConfigModal(false)
    } catch (error: any) {
      toast.error(error.message || 'Failed to save configuration')
    }
  }

  if (!gitStatus) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6 text-center">
        <GitBranch className="w-16 h-16 text-dark-500 mb-4" />
        <h2 className="text-xl font-semibold mb-2">No Git Repository</h2>
        <p className="text-dark-400 mb-6">
          This directory is not a Git repository. Initialize one to get started.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={initRepo}
            className="btn btn-primary"
          >
            <Plus className="w-4 h-4 mr-2" />
            Initialize Repository
          </button>
          
          <button
            onClick={cloneRepo}
            className="btn btn-secondary"
          >
            <Download className="w-4 h-4 mr-2" />
            Clone Repository
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-dark-900">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-dark-700 bg-dark-800">
        <div className="flex items-center space-x-3">
          <GitBranch className="w-5 h-5 text-primary-400" />
          <h2 className="text-lg font-semibold">Git</h2>
          <span className="text-sm text-dark-400">({gitStatus.branch})</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowConfigModal(true)}
            className="btn btn-ghost btn-sm"
          >
            <Settings className="w-4 h-4" />
          </button>
          
          <button
            onClick={loadGitStatus}
            disabled={isLoading}
            className="btn btn-ghost btn-sm"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Status Bar */}
      <div className="p-4 border-b border-dark-700 bg-dark-800">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <GitBranch className="w-4 h-4 text-blue-400" />
              <span className="font-medium">{gitStatus.branch}</span>
            </div>
            
            {gitStatus.ahead > 0 && (
              <div className="flex items-center space-x-1 text-green-400">
                <Upload className="w-4 h-4" />
                <span className="text-sm">{gitStatus.ahead}</span>
              </div>
            )}
            
            {gitStatus.behind > 0 && (
              <div className="flex items-center space-x-1 text-red-400">
                <Download className="w-4 h-4" />
                <span className="text-sm">{gitStatus.behind}</span>
              </div>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            {gitStatus.clean ? (
              <div className="flex items-center space-x-1 text-green-400">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm">Clean</span>
              </div>
            ) : (
              <div className="flex items-center space-x-1 text-yellow-400">
                <Clock className="w-4 h-4" />
                <span className="text-sm">Changes</span>
              </div>
            )}
          </div>
        </div>
        
        <div className="flex flex-wrap gap-2">
          <button
            onClick={createBranch}
            className="btn btn-secondary btn-sm"
          >
            <Plus className="w-4 h-4 mr-1" />
            Branch
          </button>
          
          <button
            onClick={pullChanges}
            className="btn btn-secondary btn-sm"
            disabled={gitStatus.behind === 0}
          >
            <Download className="w-4 h-4 mr-1" />
            Pull
          </button>
          
          <button
            onClick={pushChanges}
            className="btn btn-secondary btn-sm"
            disabled={gitStatus.ahead === 0}
          >
            <Upload className="w-4 h-4 mr-1" />
            Push
          </button>
        </div>
      </div>

      {/* File Changes */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {/* Staged Files */}
        {gitStatus.staged.length > 0 && (
          <div className="p-4 border-b border-dark-700">
            <h3 className="text-sm font-semibold text-green-400 mb-2">
              Staged Changes ({gitStatus.staged.length})
            </h3>
            <div className="space-y-1">
              {gitStatus.staged.map((file) => (
                <div key={file} className="flex items-center space-x-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <span className="text-dark-200">{file}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Modified Files */}
        {gitStatus.modified.length > 0 && (
          <div className="p-4 border-b border-dark-700">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-yellow-400">
                Modified Files ({gitStatus.modified.length})
              </h3>
              <button
                onClick={() => addFiles(gitStatus.modified)}
                className="btn btn-ghost btn-sm"
              >
                Stage All
              </button>
            </div>
            <div className="space-y-1">
              {gitStatus.modified.map((file) => (
                <div key={file} className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-yellow-400" />
                    <span className="text-dark-200">{file}</span>
                  </div>
                  <button
                    onClick={() => addFiles([file])}
                    className="btn btn-ghost btn-sm"
                  >
                    Stage
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Untracked Files */}
        {gitStatus.untracked.length > 0 && (
          <div className="p-4 border-b border-dark-700">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-blue-400">
                Untracked Files ({gitStatus.untracked.length})
              </h3>
              <button
                onClick={() => addFiles(gitStatus.untracked)}
                className="btn btn-ghost btn-sm"
              >
                Stage All
              </button>
            </div>
            <div className="space-y-1">
              {gitStatus.untracked.map((file) => (
                <div key={file} className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2">
                    <Plus className="w-4 h-4 text-blue-400" />
                    <span className="text-dark-200">{file}</span>
                  </div>
                  <button
                    onClick={() => addFiles([file])}
                    className="btn btn-ghost btn-sm"
                  >
                    Stage
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Branches */}
        {branches.length > 0 && (
          <div className="p-4 border-b border-dark-700">
            <h3 className="text-sm font-semibold text-purple-400 mb-2">
              Branches
            </h3>
            <div className="space-y-1">
              {branches.map((branch) => (
                <div key={branch} className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2">
                    <GitBranch className={`w-4 h-4 ${branch === gitStatus.branch ? 'text-green-400' : 'text-dark-400'}`} />
                    <span className={branch === gitStatus.branch ? 'text-green-400 font-medium' : 'text-dark-200'}>
                      {branch}
                    </span>
                  </div>
                  {branch !== gitStatus.branch && (
                    <button
                      onClick={() => switchBranch(branch)}
                      className="btn btn-ghost btn-sm"
                    >
                      Switch
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Commit Section */}
      {gitStatus.staged.length > 0 && (
        <div className="border-t border-dark-700 p-4 bg-dark-800">
          <div className="space-y-3">
            <textarea
              value={commitMessage}
              onChange={(e) => setCommitMessage(e.target.value)}
              placeholder="Enter commit message..."
              className="textarea resize-none h-20"
            />
            
            <button
              onClick={commitChanges}
              disabled={!commitMessage.trim()}
              className="btn btn-primary w-full"
            >
              <GitCommit className="w-4 h-4 mr-2" />
              Commit Changes
            </button>
          </div>
        </div>
      )}

      {/* Config Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-800 rounded-lg w-full max-w-md">
            <div className="p-4 border-b border-dark-600">
              <h3 className="text-lg font-semibold">Git Configuration</h3>
            </div>
            
            <div className="p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  <User className="w-4 h-4 inline mr-2" />
                  Name
                </label>
                <input
                  type="text"
                  value={gitConfig.name}
                  onChange={(e) => setGitConfig(prev => ({ ...prev, name: e.target.value }))}
                  className="input"
                  placeholder="Your name"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">
                  <Key className="w-4 h-4 inline mr-2" />
                  Email
                </label>
                <input
                  type="email"
                  value={gitConfig.email}
                  onChange={(e) => setGitConfig(prev => ({ ...prev, email: e.target.value }))}
                  className="input"
                  placeholder="your.email@example.com"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">
                  <Globe className="w-4 h-4 inline mr-2" />
                  Remote URL
                </label>
                <input
                  type="url"
                  value={gitConfig.remoteUrl}
                  onChange={(e) => setGitConfig(prev => ({ ...prev, remoteUrl: e.target.value }))}
                  className="input"
                  placeholder="https://github.com/user/repo.git"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-2 p-4 border-t border-dark-600">
              <button
                onClick={() => setShowConfigModal(false)}
                className="btn btn-ghost"
              >
                Cancel
              </button>
              <button
                onClick={saveGitConfig}
                className="btn btn-primary"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default GitPanel