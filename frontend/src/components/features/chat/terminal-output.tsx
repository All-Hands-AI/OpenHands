import React from 'react';
import { convertAnsiToHtml } from '#/utils/ansi-to-html';

interface TerminalOutputProps {
  content: string;
}

export function TerminalOutput({ content }: TerminalOutputProps) {
  const htmlContent = convertAnsiToHtml(content);
  
  return (
    <pre 
      className="bg-black rounded-lg p-4 overflow-x-auto"
      dangerouslySetInnerHTML={{ __html: htmlContent }}
    />
  );
}