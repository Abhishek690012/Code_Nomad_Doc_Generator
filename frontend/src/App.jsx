import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import StatusBar from './components/StatusBar';
import DocView from './components/DocView';
import QueryPanel from './components/QueryPanel';
import './styles/index.css';

function App() {
  const [docs, setDocs] = useState({});
  const [selectedFile, setSelectedFile] = useState(null);
  const [activeTab, setActiveTab] = useState('docs');
  const [queryResponse, setQueryResponse] = useState(null);
  const [isTriggering, setIsTriggering] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);

  const fileKeys = Object.keys(docs);

  // Fetch initial docs on mount
  useEffect(() => {
    fetch('http://localhost:5000/docs')
      .then((res) => res.json())
      .then((data) => {
        if (data && Object.keys(data).length > 0) {
          setDocs(data);
          setSelectedFile(Object.keys(data)[0]);
        }
      })
      .catch((err) => console.error("Error fetching docs:", err));
  }, []);

  /** Called when the user clicks "Trigger Manual Run" in the StatusBar. */
  async function handleTrigger() {
    setIsTriggering(true);
    try {
      const response = await fetch('http://localhost:5000/trigger', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ repo: "octocat/Hello-World", files: ["README"] }),
      });
      const data = await response.json();
      if (data) {
        setDocs(data);
        if (!selectedFile && Object.keys(data).length > 0) {
          setSelectedFile(Object.keys(data)[0]);
        }
      }
    } catch (err) {
      console.error("Error triggering pipeline:", err);
    } finally {
      setIsTriggering(false);
    }
  }

  /** Called when the user submits a question in the QueryPanel. */
  async function handleQuery(question) {
    setIsQuerying(true);
    setQueryResponse(null);
    try {
      const response = await fetch('http://localhost:5000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      });
      const data = await response.json();
      setQueryResponse(data);
    } catch (err) {
      console.error("Error querying codebase:", err);
    } finally {
      setIsQuerying(false);
    }
  }

  return (
    <div className="app-container">
      {/* ── Left: Sidebar ── */}
      <Sidebar
        files={fileKeys}
        selectedFile={selectedFile}
        onSelectFile={setSelectedFile}
      />

      {/* ── Right: Main Panel ── */}
      <main className="main-panel">
        {/* Top: Status Bar */}
        <StatusBar
          onTrigger={handleTrigger}
          isTriggering={isTriggering}
          stats={{ filesIndexed: fileKeys.length, lastRun: 'Just now' }}
        />

        {/* Page title */}
        <header className="main-header">
          <h1>
            {activeTab === 'docs'
              ? (selectedFile || 'No file selected')
              : 'Ask the Codebase'}
          </h1>
        </header>

        {/* ── Tab Navigation ── */}
        <nav className="tab-nav" role="tablist" aria-label="View panels">
          <button
            id="tab-docs"
            role="tab"
            aria-selected={activeTab === 'docs'}
            className={`tab-btn ${activeTab === 'docs' ? 'tab-btn--active' : ''}`}
            onClick={() => setActiveTab('docs')}
          >
            <span className="tab-btn-icon">📄</span>
            Documentation
          </button>
          <button
            id="tab-query"
            role="tab"
            aria-selected={activeTab === 'query'}
            className={`tab-btn ${activeTab === 'query' ? 'tab-btn--active' : ''}`}
            onClick={() => setActiveTab('query')}
          >
            <span className="tab-btn-icon">💬</span>
            Ask the Codebase
          </button>
        </nav>

        {/* ── Panel Content ── */}
        <div className="main-content">
          {activeTab === 'docs' && (
            <DocView fileData={docs[selectedFile]} />
          )}
          {activeTab === 'query' && (
            <QueryPanel
              queryResponse={queryResponse}
              onSubmitQuery={handleQuery}
              isQuerying={isQuerying}
            />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
