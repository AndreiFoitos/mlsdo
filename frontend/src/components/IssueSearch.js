import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = '/api';

function IssueSearch() {
  const [keyword, setKeyword] = useState('');
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searched, setSearched] = useState(false);
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);

  const handleSearch = async (e, newOffset = 0) => {
    if (e) e.preventDefault();
    
    if (!keyword.trim()) {
      setError('Please enter a search keyword');
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(true);
    setOffset(newOffset);

    try {
      console.log('Searching for:', keyword, 'offset:', newOffset);
      
      const response = await axios.get(`${API_BASE_URL}/issues/search`, {
        params: {
          keyword: keyword.trim(),
          limit: limit,
          offset: newOffset
        }
      });

      console.log('Search results:', response.data);
      
      setResults(response.data.results || []);
      setTotal(response.data.total || 0);
      setLoading(false);
    } catch (err) {
      console.error('Search error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to search issues');
      setResults([]);
      setTotal(0);
      setLoading(false);
    }
  };

  const handleReset = () => {
    setKeyword('');
    setResults([]);
    setTotal(0);
    setError(null);
    setSearched(false);
    setOffset(0);
  };

  const handleNextPage = () => {
    if (offset + limit < total) {
      handleSearch(null, offset + limit);
    }
  };

  const handlePrevPage = () => {
    if (offset > 0) {
      handleSearch(null, Math.max(0, offset - limit));
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return 'Invalid date';
    }
  };

  const highlightKeyword = (text, keyword) => {
    if (!text || !keyword) return text;
    
    const regex = new RegExp(`(${keyword})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, i) => 
      regex.test(part) ? <mark key={i}>{part}</mark> : part
    );
  };

  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.ceil(total / limit);

  return (
    <div className="prediction-container">
      <h2>Search Issues</h2>
      <p>Search for issues in the database using keywords</p>

      <form onSubmit={handleSearch} className="search-form">
        <div className="search-input-group">
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="Enter keyword to search (e.g., authentication, refactor, API)..."
            disabled={loading}
            className="search-input"
          />
          <button type="submit" disabled={loading || !keyword.trim()} className="btn-primary">
            {loading ? 'Searching...' : 'Search'}
          </button>
          <button type="button" onClick={handleReset} className="btn-secondary">
            Reset
          </button>
        </div>
      </form>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {searched && !loading && !error && (
        <div className="search-results-summary">
          <p>
            Found <strong>{total}</strong> issue{total !== 1 ? 's' : ''} matching 
            <em> "{keyword}"</em>
          </p>
          {totalPages > 1 && (
            <p className="pagination-info">
              Showing page <strong>{currentPage}</strong> of <strong>{totalPages}</strong>
            </p>
          )}
        </div>
      )}

      {results.length > 0 && (
        <>
          <div className="search-results">
            {results.map((issue, index) => (
              <div key={issue.id || index} className="search-result-card">
                <div className="result-header">
                  <h4>{highlightKeyword(issue.summary, keyword)}</h4>
                  {issue.label && (
                    <span className={`label-badge ${issue.label.toLowerCase().replace('-', '')}`}>
                      {issue.label}
                    </span>
                  )}
                </div>
                
                <p className="result-description">
                  {highlightKeyword(
                    issue.description?.substring(0, 300) + (issue.description?.length > 300 ? '...' : ''),
                    keyword
                  )}
                </p>
                
                <div className="result-meta">
                  {issue.id && <span>ID: {issue.id}</span>}
                  {issue.created_at && <span>{formatDate(issue.created_at)}</span>}
                  {issue.prediction && (
                    <span className="prediction-badge">
                      Predicted: {issue.prediction}
                      {issue.confidence && ` (${(issue.confidence * 100).toFixed(0)}%)`}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button 
                onClick={handlePrevPage} 
                disabled={offset === 0 || loading}
                className="btn-secondary"
              >
                ← Previous
              </button>
              
              <span className="page-indicator">
                Page {currentPage} of {totalPages}
              </span>
              
              <button 
                onClick={handleNextPage} 
                disabled={offset + limit >= total || loading}
                className="btn-secondary"
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}

      {searched && results.length === 0 && !loading && !error && (
        <div className="no-results">
          <div className="no-results-icon"></div>
          <h3>No issues found</h3>
          <p>No issues found matching "<strong>{keyword}</strong>"</p>
          <p>Try different keywords or check your spelling.</p>
        </div>
      )}

      <div className="info-box" style={{marginTop: '2rem'}}>
        <h4>Search Tips</h4>
        <ul>
          <li>Search looks through both summary and description fields</li>
          <li>Search is case-insensitive (e.g., "API" matches "api")</li>
          <li>Use specific keywords for better results</li>
          <li>Partial word matches are supported</li>
        </ul>
        <h4 style={{marginTop: '1rem'}}>Example searches:</h4>
        <div className="search-examples">
          <button onClick={() => { setKeyword('authentication'); handleSearch(); }} className="example-btn">authentication</button>
          <button onClick={() => { setKeyword('refactor'); handleSearch(); }} className="example-btn">refactor</button>
          <button onClick={() => { setKeyword('API'); handleSearch(); }} className="example-btn">API</button>
          <button onClick={() => { setKeyword('database'); handleSearch(); }} className="example-btn">database</button>
        </div>
      </div>
    </div>
  );
}

export default IssueSearch;