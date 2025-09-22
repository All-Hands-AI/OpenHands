import React, { useRef, useCallback, useState } from "react";

interface UseFileHandlingReturn {
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  chatContainerRef: React.RefObject<HTMLDivElement | null>;
  isDragOver: boolean;
  handleFileIconClick: (isDisabled: boolean) => void;
  handleFileInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleDragOver: (e: React.DragEvent, isDisabled: boolean) => void;
  handleDragLeave: (e: React.DragEvent, isDisabled: boolean) => void;
  handleDrop: (e: React.DragEvent, isDisabled: boolean) => void;
}

/**
 * Hook for handling file operations (upload, drag & drop)
 */
export const useFileHandling = (
  onFilesPaste?: (files: File[]) => void,
): UseFileHandlingReturn => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const chatContainerRef = useRef<HTMLDivElement | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  // Function to add files and notify parent
  const addFiles = useCallback(
    (files: File[]) => {
      if (onFilesPaste && files.length > 0) {
        onFilesPaste(files);
      }
    },
    [onFilesPaste],
  );

  // File icon click handler
  const handleFileIconClick = useCallback((isDisabled: boolean) => {
    if (!isDisabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, []);

  // File input change handler
  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);
      addFiles(files);
    },
    [addFiles],
  );

  // Drag and drop event handlers
  const handleDragOver = useCallback(
    (e: React.DragEvent, isDisabled: boolean) => {
      if (isDisabled) {
        return;
      }
      e.preventDefault();
      setIsDragOver(true);
    },
    [],
  );

  const handleDragLeave = useCallback(
    (e: React.DragEvent, isDisabled: boolean) => {
      if (
        isDisabled ||
        chatContainerRef.current?.contains(e.relatedTarget as Node)
      ) {
        return;
      }

      e.preventDefault();
      setIsDragOver(false);
    },
    [],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent, isDisabled: boolean) => {
      if (isDisabled) {
        return;
      }

      e.preventDefault();

      setIsDragOver(false);

      const files = Array.from(e.dataTransfer.files);
      addFiles(files);
    },
    [addFiles],
  );

  return {
    fileInputRef,
    chatContainerRef,
    isDragOver,
    handleFileIconClick,
    handleFileInputChange,
    handleDragOver,
    handleDragLeave,
    handleDrop,
  };
};
