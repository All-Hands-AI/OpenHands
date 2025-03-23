import { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { QueryKeys } from '#/utils/query/query-keys';

/**
 * Interface for file state
 */
export interface FileState {
  path: string;
  savedContent: string;
  unsavedContent: string;
  changed: boolean;
}

/**
 * Custom hook for managing file states
 * This replaces the Redux file-state-slice and parts of code-slice
 */
export function useFileState() {
  const queryClient = useQueryClient();
  const [fileStates, setFileStates] = useState<FileState[]>([]);

  /**
   * Add or update a file state
   */
  const addOrUpdateFileState = useCallback((fileState: Omit<FileState, 'changed'>) => {
    const { path, savedContent, unsavedContent } = fileState;
    const changed = savedContent !== unsavedContent;
    
    setFileStates(prevStates => {
      const newStates = prevStates.filter(state => state.path !== path);
      return [...newStates, { path, savedContent, unsavedContent, changed }];
    });
    
    // Invalidate file query to ensure UI reflects the latest state
    queryClient.invalidateQueries({ 
      queryKey: QueryKeys.file(path.split('/').pop() || '', path)
    });
  }, [queryClient]);

  /**
   * Remove a file state
   */
  const removeFileState = useCallback((path: string) => {
    setFileStates(prevStates => prevStates.filter(state => state.path !== path));
  }, []);

  /**
   * Check if a file has been changed
   */
  const isFileChanged = useCallback((path: string) => {
    const fileState = fileStates.find(state => state.path === path);
    return fileState ? fileState.changed : false;
  }, [fileStates]);

  /**
   * Get a file state by path
   */
  const getFileState = useCallback((path: string) => {
    return fileStates.find(state => state.path === path);
  }, [fileStates]);

  /**
   * Reset all file states
   */
  const resetFileStates = useCallback(() => {
    setFileStates([]);
  }, []);

  return {
    fileStates,
    addOrUpdateFileState,
    removeFileState,
    isFileChanged,
    getFileState,
    resetFileStates
  };
}