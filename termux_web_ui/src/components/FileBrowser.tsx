import React, { useState, useEffect } from 'react'
import { 
  Folder, 
  File, 
  ArrowLeft, 
  Home, 
  RefreshCw, 
  Plus, 
  Edit3, 
  Trash2, 
  Download,
  Upload,
  Search,
  Eye,
  Copy,
  Scissors,
  FolderPlus
} from 'lucide-react'
import toast from 'react-hot-toast'

import { fileApi } from '../services/api'

interface FileItem {
  name: string
  type: 'file' | 'directory'
  size: number
  path: string
}

function FileBrowser() {
  const [currentPath, setCurrentPath] = useState('/data/data/com.termux/files/home')
  const [files, setFiles] = useState<FileItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createType, setCreateType] = useState<'file' | 'folder'>('file')
  const [createName, setCreateName] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [clipboard, setClipboard] = useState<{ item: FileItem; operation: 'copy' | 'cut' } | null>(null)

  const loadFiles = async (path: string) => {
    setIsLoading(true)
    try {
      const result = await fileApi.listDirectory(path)
      if (result.success && result.data) {
        const filesWithPath = result.data.map(file => ({
          ...file,
          path: `${path}/${file.name}`.replace(/\/+/g, '/')
        }))
        setFiles(filesWithPath)
        setCurrentPath(path)
      } else {
        toast.error(result.error || 'Failed to load directory')
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to load directory')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadFiles(currentPath)
  }, [])

  const navigateUp = () => {
    const parentPath = currentPath.split('/').slice(0, -1).join('/') || '/'
    loadFiles(parentPath)
  }

  const navigateToHome = () => {
    loadFiles('/data/data/com.termux/files/home')
  }

  const openFile = async (file: FileItem) => {
    if (file.type === 'directory') {
      loadFiles(file.path)
    } else {
      setSelectedFile(file)
      // For text files, we could show a preview or editor
      if (file.name.match(/\.(txt|md|py|js|ts|json|xml|html|css|sh|conf|log)$/i)) {
        try {
          const result = await fileApi.readFile(file.path)
          if (result.success) {
            // Show file content in a modal or editor
            showFileContent(file, result.data!)
          }
        } catch (error: any) {
          toast.error('Failed to read file')
        }
      }
    }
  }

  const showFileContent = (file: FileItem, content: string) => {
    // Create a simple modal to show file content
    const modal = document.createElement('div')
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4'
    modal.innerHTML = `
      <div class="bg-dark-800 rounded-lg max-w-4xl w-full max-h-[80vh] overflow-hidden">
        <div class="flex items-center justify-between p-4 border-b border-dark-600">
          <h3 class="text-lg font-semibold text-white">${file.name}</h3>
          <button class="text-dark-400 hover:text-white" onclick="this.closest('.fixed').remove()">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        <div class="p-4 overflow-auto max-h-[60vh]">
          <pre class="text-sm text-dark-200 whitespace-pre-wrap font-mono">${content.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
        </div>
      </div>
    `
    document.body.appendChild(modal)
  }

  const createItem = async () => {
    if (!createName.trim()) {
      toast.error('Please enter a name')
      return
    }

    const newPath = `${currentPath}/${createName}`.replace(/\/+/g, '/')

    try {
      if (createType === 'file') {
        const result = await fileApi.writeFile(newPath, '')
        if (result.success) {
          toast.success('File created successfully')
          loadFiles(currentPath)
        } else {
          toast.error(result.error || 'Failed to create file')
        }
      } else {
        // Create directory using command
        const result = await fetch('/api/system/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ command: `mkdir -p "${newPath}"` })
        })
        
        if (result.ok) {
          toast.success('Folder created successfully')
          loadFiles(currentPath)
        } else {
          toast.error('Failed to create folder')
        }
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to create item')
    }

    setShowCreateModal(false)
    setCreateName('')
  }

  const deleteItem = async (file: FileItem) => {
    if (!confirm(`Are you sure you want to delete ${file.name}?`)) return

    try {
      const command = file.type === 'directory' ? `rm -rf "${file.path}"` : `rm "${file.path}"`
      const result = await fetch('/api/system/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
      })

      if (result.ok) {
        toast.success(`${file.type === 'directory' ? 'Folder' : 'File'} deleted successfully`)
        loadFiles(currentPath)
      } else {
        toast.error('Failed to delete item')
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to delete item')
    }
  }

  const copyToClipboard = (file: FileItem) => {
    setClipboard({ item: file, operation: 'copy' })
    toast.success(`${file.name} copied to clipboard`)
  }

  const cutToClipboard = (file: FileItem) => {
    setClipboard({ item: file, operation: 'cut' })
    toast.success(`${file.name} cut to clipboard`)
  }

  const pasteFromClipboard = async () => {
    if (!clipboard) return

    const sourcePath = clipboard.item.path
    const targetPath = `${currentPath}/${clipboard.item.name}`.replace(/\/+/g, '/')

    try {
      const command = clipboard.operation === 'copy' 
        ? `cp -r "${sourcePath}" "${targetPath}"`
        : `mv "${sourcePath}" "${targetPath}"`

      const result = await fetch('/api/system/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
      })

      if (result.ok) {
        toast.success(`${clipboard.item.name} ${clipboard.operation === 'copy' ? 'copied' : 'moved'} successfully`)
        loadFiles(currentPath)
        if (clipboard.operation === 'cut') {
          setClipboard(null)
        }
      } else {
        toast.error(`Failed to ${clipboard.operation} item`)
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to paste item')
    }
  }

  const formatFileSize = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB']
    let size = bytes
    let unitIndex = 0
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024
      unitIndex++
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`
  }

  const filteredFiles = files.filter(file =>
    file.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="flex flex-col h-full bg-dark-900">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-dark-700 bg-dark-800">
        <div className="flex items-center space-x-3">
          <Folder className="w-5 h-5 text-primary-400" />
          <h2 className="text-lg font-semibold">File Browser</h2>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary btn-sm"
          >
            <Plus className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => loadFiles(currentPath)}
            disabled={isLoading}
            className="btn btn-ghost btn-sm"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex items-center space-x-2 p-4 border-b border-dark-700 bg-dark-800">
        <button
          onClick={navigateToHome}
          className="btn btn-ghost btn-sm"
          title="Home"
        >
          <Home className="w-4 h-4" />
        </button>
        
        <button
          onClick={navigateUp}
          className="btn btn-ghost btn-sm"
          disabled={currentPath === '/'}
          title="Up"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        
        <div className="flex-1 text-sm text-dark-300 font-mono bg-dark-700 px-3 py-1 rounded">
          {currentPath}
        </div>
        
        {clipboard && (
          <button
            onClick={pasteFromClipboard}
            className="btn btn-secondary btn-sm"
            title={`Paste ${clipboard.item.name}`}
          >
            Paste
          </button>
        )}
      </div>

      {/* Search */}
      <div className="p-4 border-b border-dark-700">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-dark-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search files and folders..."
            className="input pl-10"
          />
        </div>
      </div>

      {/* File List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin text-primary-500" />
          </div>
        ) : filteredFiles.length === 0 ? (
          <div className="text-center py-12 text-dark-400">
            {searchQuery ? 'No files match your search' : 'This folder is empty'}
          </div>
        ) : (
          <div className="divide-y divide-dark-700">
            {filteredFiles.map((file) => (
              <div
                key={file.path}
                className="flex items-center justify-between p-4 hover:bg-dark-800 transition-colors group"
              >
                <div 
                  className="flex items-center space-x-3 flex-1 cursor-pointer"
                  onClick={() => openFile(file)}
                >
                  {file.type === 'directory' ? (
                    <Folder className="w-5 h-5 text-blue-400" />
                  ) : (
                    <File className="w-5 h-5 text-dark-400" />
                  )}
                  
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-dark-200 truncate">
                      {file.name}
                    </div>
                    <div className="text-xs text-dark-500">
                      {file.type === 'file' && formatFileSize(file.size)}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => copyToClipboard(file)}
                    className="p-1 text-dark-400 hover:text-dark-200 transition-colors"
                    title="Copy"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  
                  <button
                    onClick={() => cutToClipboard(file)}
                    className="p-1 text-dark-400 hover:text-dark-200 transition-colors"
                    title="Cut"
                  >
                    <Scissors className="w-4 h-4" />
                  </button>
                  
                  <button
                    onClick={() => deleteItem(file)}
                    className="p-1 text-dark-400 hover:text-red-400 transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-800 rounded-lg w-full max-w-md">
            <div className="p-4 border-b border-dark-600">
              <h3 className="text-lg font-semibold">Create New</h3>
            </div>
            
            <div className="p-4 space-y-4">
              <div className="flex space-x-2">
                <button
                  onClick={() => setCreateType('file')}
                  className={`btn ${createType === 'file' ? 'btn-primary' : 'btn-secondary'}`}
                >
                  <File className="w-4 h-4 mr-2" />
                  File
                </button>
                <button
                  onClick={() => setCreateType('folder')}
                  className={`btn ${createType === 'folder' ? 'btn-primary' : 'btn-secondary'}`}
                >
                  <FolderPlus className="w-4 h-4 mr-2" />
                  Folder
                </button>
              </div>
              
              <input
                type="text"
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                placeholder={`Enter ${createType} name...`}
                className="input"
                autoFocus
                onKeyPress={(e) => e.key === 'Enter' && createItem()}
              />
            </div>
            
            <div className="flex justify-end space-x-2 p-4 border-t border-dark-600">
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn btn-ghost"
              >
                Cancel
              </button>
              <button
                onClick={createItem}
                className="btn btn-primary"
                disabled={!createName.trim()}
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default FileBrowser