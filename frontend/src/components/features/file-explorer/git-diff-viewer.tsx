import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface GitDiffViewerProps {
  diff: string;
}

export const GitDiffViewer: React.FC<GitDiffViewerProps> = ({ diff }) => {
  return (
    <div className="git-diff-viewer">
      <SyntaxHighlighter
        language="diff"
        style={vscDarkPlus}
        showLineNumbers={true}
        wrapLines={true}
      >
        {diff}
      </SyntaxHighlighter>
    </div>
  );
};