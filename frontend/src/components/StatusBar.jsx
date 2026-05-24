import React from 'react';

/**
 * StatusBar
 * ---------
 * Top bar of the main panel. Displays at-a-glance pipeline statistics
 * on the left, and a trigger button on the right.
 *
 * Props
 * -----
 * onTrigger    {function}  Called when the "Trigger Manual Run" button is clicked.
 * stats        {object}    Optional stats object: { filesIndexed, lastRun }.
 *                          Falls back to sensible defaults if not provided.
 * isTriggering {boolean}   Indicates if the pipeline is currently running.
 */
function StatusBar({ onTrigger, stats = {}, isTriggering }) {
  const { filesIndexed = 3, lastRun = 'Just now' } = stats;

  return (
    <div className="status-bar">
      {/* ── Left side: stats ── */}
      <div className="status-stats">
        <span className="status-stat">
          <span className="status-stat-label">Files Indexed</span>
          <span className="status-stat-value">{filesIndexed}</span>
        </span>
        <span className="status-divider" aria-hidden="true">|</span>
        <span className="status-stat">
          <span className="status-stat-label">Last Run</span>
          <span className="status-stat-value">{lastRun}</span>
        </span>
        <span className="status-pulse" title="System active" />
      </div>

      {/* ── Right side: action ── */}
      <button
        id="trigger-pipeline-btn"
        className="btn-trigger"
        onClick={onTrigger}
        type="button"
        disabled={isTriggering}
      >
        <span className="btn-trigger-icon">{isTriggering ? '⏳' : '▶'}</span>
        {isTriggering ? 'Processing...' : 'Trigger Manual Run'}
      </button>
    </div>
  );
}

export default StatusBar;
