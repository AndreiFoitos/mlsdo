import React, { useState } from 'react';
import './App.css';
import SinglePrediction from './components/SinglePrediction';
import BatchPrediction from './components/BatchPrediction';
import IssueSearch from './components/IssueSearch';
import LabelSubmission from './components/LabelSubmission';

function App() {
  const [activeTab, setActiveTab] = useState('single');

  return (
    <div className="App">
      <header className="App-header">
        <h1>🏗️ Architectural Design Decision Detector</h1>
        <p>Classify Jira issues as ADD or non-ADD</p>
      </header>

      <nav className="tab-navigation">
        <button 
          className={activeTab === 'single' ? 'active' : ''}
          onClick={() => setActiveTab('single')}
        >
          Single Prediction
        </button>
        <button 
          className={activeTab === 'batch' ? 'active' : ''}
          onClick={() => setActiveTab('batch')}
        >
          Batch Prediction
        </button>
        <button 
          className={activeTab === 'search' ? 'active' : ''}
          onClick={() => setActiveTab('search')}
        >
          Search Issues
        </button>
        <button 
          className={activeTab === 'label' ? 'active' : ''}
          onClick={() => setActiveTab('label')}
        >
          Submit Label (Bonus)
        </button>
      </nav>

      <main className="main-content">
        {activeTab === 'single' && <SinglePrediction />}
        {activeTab === 'batch' && <BatchPrediction />}
        {activeTab === 'search' && <IssueSearch />}
        {activeTab === 'label' && <LabelSubmission />}
      </main>

      <footer className="App-footer">
        <p>MLSDO Assignment 2025 | University of Groningen</p>
      </footer>
    </div>
  );
}

export default App;