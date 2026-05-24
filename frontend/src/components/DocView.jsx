import React from 'react';

/**
 * DocView
 * -------
 * Displays the AI-generated documentation for a selected file.
 *
 * Props
 * -----
 * fileData  {object|null}  Object with `summary` (string) and `functions` (array).
 *                          Renders a placeholder when null / undefined.
 */
function DocView({ fileData }) {
  if (!fileData) {
    return (
      <div className="placeholder-content">
        <div className="placeholder-inner">
          <span className="placeholder-icon">📂</span>
          <p>Select a file from the sidebar to view its documentation.</p>
        </div>
      </div>
    );
  }

  const { summary, functions = [] } = fileData;

  return (
    <div className="doc-view">
      {/* ── File Summary ── */}
      <section className="doc-section">
        <h2 className="doc-section-title">
          <span className="doc-section-icon">📋</span>
          File Summary
        </h2>
        <p className="doc-summary">{summary}</p>
      </section>

      {/* ── Functions ── */}
      {functions.length > 0 && (
        <section className="doc-section">
          <h2 className="doc-section-title">
            <span className="doc-section-icon">⚙️</span>
            Functions
            <span className="doc-count">{functions.length}</span>
          </h2>
          <ul className="func-list">
            {functions.map((fn) => (
              <li key={fn.name} className="func-item">
                <h3 className="func-name">{fn.name}</h3>
                <p className="func-desc">{fn.description}</p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

export default DocView;
