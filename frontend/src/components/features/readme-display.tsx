import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface ReadmeFile {
  path: string;
  content: string;
}

const ITEMS_PER_PAGE = 10;

function renderReadmeTree(files: ReadmeFile[]) {
  const tree = {};

  files.forEach(file => {
    const parts = file.path.split('/');
    let current = tree;

    parts.forEach((part, index) => {
      if (!current[part]) {
        current[part] = index === parts.length - 1 ? file.content : {};
      }
      current = current[part];
    });
  });

  function renderTree(node, path = '') {
    const [collapsed, setCollapsed] = useState(true);

    return Object.keys(node).map(key => (
      <div key={path + key} style={{ marginLeft: '20px' }}>
        <strong onClick={() => setCollapsed(!collapsed)} style={{ cursor: 'pointer' }}>
          {key}
        </strong>
        {!collapsed && (
          typeof node[key] === 'string' ? (
            <div>
              <ReactMarkdown>{node[key]}</ReactMarkdown>
              <button onClick={() => downloadFile(node[key], key)}>Download</button>
            </div>
          ) : (
            renderTree(node[key], path + key + '/')
          )
        )}
      </div>
    ));
  }

  return renderTree(tree);
}

function downloadFile(content, filename) {
  const blob = new Blob([content], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function ReadmeDisplay() {
  const [readmeFiles, setReadmeFiles] = useState<ReadmeFile[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/readme-files')
      .then(response => response.json())
      .then(data => setReadmeFiles(data))
      .catch(error => setError('Error fetching README files'));
  }, []);

  const totalPages = Math.ceil(readmeFiles.length / ITEMS_PER_PAGE);
  const currentFiles = readmeFiles.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const handlePageChange = (newPage: number) => {
    if (newPage > 0 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  const filteredFiles = currentFiles.filter(file =>
    file.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
    file.content.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="readme-container">
      <input
        type="text"
        placeholder="Search README files..."
        value={searchTerm}
        onChange={e => setSearchTerm(e.target.value)}
        className="search-bar"
      />
      {renderReadmeTree(filteredFiles)}
      <div className="pagination">
        <button onClick={() => handlePageChange(currentPage - 1)}>Previous</button>
        <span>Page {currentPage} of {totalPages}</span>
        <button onClick={() => handlePageChange(currentPage + 1)}>Next</button>
      </div>
    </div>
  );
}