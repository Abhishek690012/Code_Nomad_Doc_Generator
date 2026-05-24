import React from 'react';

/**
 * Sidebar
 * -------
 * Left-hand navigation panel that lists all indexed files.
 *
 * Props
 * -----
 * files        {string[]}   Array of filename strings to display.
 * selectedFile {string}     The currently active filename.
 * onSelectFile {function}   Called with the filename when a row is clicked.
 */
function Sidebar({ files = [], selectedFile, onSelectFile }) {
  return (
    <aside className="sidebar">
      {/* Brand / header */}
      <div className="sidebar-brand">
        <span className="sidebar-brand-icon">⚡</span>
        <span className="sidebar-brand-name">Codewise</span>
      </div>

      <h2 className="sidebar-title">Indexed Files</h2>

      {files.length === 0 ? (
        <p className="sidebar-empty">No files indexed yet.</p>
      ) : (
        <ul className="file-list">
          {files.map((filename) => (
            <li
              key={filename}
              className={`file-item ${selectedFile === filename ? 'active-file' : ''}`}
              onClick={() => onSelectFile(filename)}
              title={filename}
            >
              <span className="file-icon">📄</span>
              <span className="file-name">{filename}</span>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}

export default Sidebar;
