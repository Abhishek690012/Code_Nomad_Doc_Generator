import React, { useState } from 'react';
import { mockDocs } from './mockData';
import './styles/index.css';

function App() {
  const fileKeys = Object.keys(mockDocs);
  // Default to the first key in the mock data, or null if empty
  const [selectedFile, setSelectedFile] = useState(
    fileKeys.length > 0 ? fileKeys[0] : null
  );

  return (
    <div className="app-container">
      {/* Sidebar Panel */}
      <aside className="sidebar">
        <h2 className="sidebar-title">Files</h2>
        <ul className="file-list">
          {fileKeys.map((fileName) => (
            <li
              key={fileName}
              className={`file-item ${selectedFile === fileName ? 'active' : ''}`}
              onClick={() => setSelectedFile(fileName)}
            >
              <span className="file-icon">📄</span>
              <span className="file-name">{fileName}</span>
            </li>
          ))}
        </ul>
      </aside>

      {/* Main Panel */}
      <main className="main-panel">
        <header className="main-header">
          <h1>{selectedFile || 'No file selected'}</h1>
        </header>
        <div className="main-content">
          {/* Future complex sub-components will go here */}
          {selectedFile ? (
            <div className="placeholder-content">
              <p>Documentation and Q&A content for <strong>{selectedFile}</strong> will be displayed here.</p>
            </div>
          ) : (
            <div className="placeholder-content">
              <p>Please select a file from the sidebar.</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
