import React, { useState } from 'react';

/**
 * QueryPanel
 * ----------
 * "Ask the Codebase" Q&A panel. Lets the user type a natural-language
 * question and displays the AI's answer alongside a code snippet and citation.
 *
 * Props
 * -----
 * queryResponse  {object|null}  Object with `answer`, `source_file`,
 *                               `function_name`, and `snippet`.
 * onSubmitQuery  {function}     Called with the question string on submit.
 * isQuerying     {boolean}      Indicates if a query is currently running.
 */
function QueryPanel({ queryResponse, onSubmitQuery, isQuerying }) {
  const [question, setQuestion] = useState('');

  function handleSubmit(e) {
    e.preventDefault();
    if (isQuerying) return;
    const trimmed = question.trim();
    if (!trimmed) return;
    onSubmitQuery(trimmed);
    setQuestion('');
  }

  return (
    <div className="query-panel">
      {/* ── Input Area ── */}
      <section className="query-input-section">
        <h2 className="doc-section-title">
          <span className="doc-section-icon">🔍</span>
          Ask the Codebase
        </h2>
        <form className="query-form" onSubmit={handleSubmit}>
          <textarea
            id="query-input"
            className="query-textarea"
            placeholder="e.g. How does authentication work in this codebase?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
            onKeyDown={(e) => {
              /* Submit on Ctrl+Enter / Cmd+Enter */
              if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') handleSubmit(e);
            }}
            disabled={isQuerying}
          />
          <div className="query-form-footer">
            <span className="query-hint">Press Ctrl+Enter to submit</span>
            <button
              id="query-submit-btn"
              type="submit"
              className="btn-query-submit"
              disabled={!question.trim() || isQuerying}
            >
              <span className="btn-query-icon">{isQuerying ? '⏳' : '✦'}</span>
              {isQuerying ? 'Thinking...' : 'Submit'}
            </button>
          </div>
        </form>
      </section>

      {/* ── Thinking Indicator ── */}
      {isQuerying && (
        <div className="query-empty">
          <span className="query-empty-icon" style={{ animation: 'pulse-ring 2s infinite' }}>🧠</span>
          <p>Thinking about your question...</p>
        </div>
      )}

      {/* ── Result Area ── */}
      {queryResponse && !isQuerying && (
        <section className="query-result-section">
          <h2 className="doc-section-title">
            <span className="doc-section-icon">💡</span>
            AI Answer
          </h2>

          <p className="query-answer">{queryResponse.answer}</p>

          {/* Code snippet */}
          {queryResponse.snippet && (
             <div className="query-snippet-wrapper">
               <div className="query-snippet-header">
                 <span className="query-snippet-lang">python</span>
               </div>
               <pre className="query-code-block">
                 <code>{queryResponse.snippet}</code>
               </pre>
             </div>
          )}

          {/* Citation pill */}
          {(queryResponse.source_file || queryResponse.function_name) && (
             <div className="query-citation">
               <span className="citation-label">Source</span>
               <span className="citation-pill">
                 {queryResponse.source_file && <span className="citation-file">{queryResponse.source_file}</span>}
                 {queryResponse.source_file && queryResponse.function_name && <span className="citation-sep">›</span>}
                 {queryResponse.function_name && <span className="citation-fn">{queryResponse.function_name}</span>}
               </span>
             </div>
          )}
        </section>
      )}

      {/* Empty state when there's no response yet */}
      {!queryResponse && !isQuerying && (
        <div className="query-empty">
          <span className="query-empty-icon">🤖</span>
          <p>Ask a question above to get an AI-powered answer about your codebase.</p>
        </div>
      )}
    </div>
  );
}

export default QueryPanel;
