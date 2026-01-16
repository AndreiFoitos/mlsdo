import React, { useState, useEffect } from 'react';
import './App.css';
import SinglePrediction from './components/SinglePrediction';
import BatchPrediction from './components/BatchPrediction';
import IssueSearch from './components/IssueSearch';
import LabelSubmission from './components/LabelSubmission';

function App() {
  const [activeTab, setActiveTab] = useState('single');
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Fetch stats on mount
    fetch('/api/stats')
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setIsLoading(false);
      })
      .catch(() => setIsLoading(false));
  }, []);

  const tabs = [
    { id: 'single', label: 'Single Prediction', icon: '▸', description: 'Classify one issue' },
    { id: 'batch', label: 'Batch Processing', icon: '≡', description: 'Multiple issues at once' },
    { id: 'search', label: 'Search Database', icon: '⌕', description: 'Find existing issues' },
    { id: 'label', label: 'Contribute Data', icon: '+', description: 'Help improve the model' }
  ];

  return (
    <div className="App">
      {/* Hero Header */}
      <header className="hero-header">
        <div className="hero-background">
          <div className="hero-gradient"></div>
          <div className="hero-pattern"></div>
        </div>
        
        <div className="hero-content">

          <h1 className="hero-title">
            Architectural Design Decision
            <span className="gradient-text"> Detector</span>
          </h1>
          
          <p className="hero-subtitle">
            AI-powered classification system for identifying architectural design decisions in issue tracking systems
          </p>
          
          {!isLoading && stats && (
            <div className="hero-stats">
              <div className="stat-item">
                <div className="stat-value">{stats.total_issues?.toLocaleString() || 0}</div>
                <div className="stat-label">Issues Analyzed</div>
              </div>
              <div className="stat-divider"></div>
              <div className="stat-item">
                <div className="stat-value">{stats.total_labeled?.toLocaleString() || 0}</div>
                <div className="stat-label">Contributions</div>
              </div>
              <div className="stat-divider"></div>
              <div className="stat-item">
                <div className="stat-value">v{stats.api_version || '1.0'}</div>
                <div className="stat-label">API Version</div>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="navigation-container">
        <div className="navigation-wrapper">
          <div className="tab-list">
            {tabs.map(tab => (
              <button
                key={tab.id}
                className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span className="tab-icon">{tab.icon}</span>
                <div className="tab-content">
                  <span className="tab-label">{tab.label}</span>
                  <span className="tab-description">{tab.description}</span>
                </div>
                {activeTab === tab.id && <div className="tab-indicator"></div>}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        <div className="content-wrapper">
          <div className="content-card">
            <div className={`tab-content-area fade-in ${activeTab}`}>
              {activeTab === 'single' && <SinglePrediction />}
              {activeTab === 'batch' && <BatchPrediction />}
              {activeTab === 'search' && <IssueSearch />}
              {activeTab === 'label' && <LabelSubmission />}
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-content">
          <div className="footer-section">
            <h4>MLSDO Assignment 2025</h4>
            <p>Machine Learning Systems Deployment & Optimizations</p>
          </div>
          <div className="footer-section">
            <h4>University of Groningen</h4>
            <p>Faculty of Science and Engineering</p>
          </div>
          <div className="footer-section">
            <h4>Technology Stack</h4>
            <div className="tech-badges">
              <span className="tech-badge">React</span>
              <span className="tech-badge">FastAPI</span>
              <span className="tech-badge">PyTorch</span>
              <span className="tech-badge">MLflow</span>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© 2025 ADD Detection System. Built with precision and care.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;