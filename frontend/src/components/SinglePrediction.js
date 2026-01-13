import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = '/api';

function SinglePrediction() {
  const [summary, setSummary] = useState('');
  const [description, setDescription] = useState('');
  const [taskId, setTaskId] = useState(null);
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [polling, setPolling] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setStatus(null);
    setPolling(false);

    try {
      console.log('Submitting prediction:', { summary, description });
      
      const response = await axios.post(`${API_BASE_URL}/predictions`, {
        summary: summary.trim(),
        description: description.trim()
      });

      console.log('Prediction submitted:', response.data);
      
      const newTaskId = response.data.task_id;
      setTaskId(newTaskId);
      setStatus('PENDING');
      setPolling(true);

      // Start polling for results
      pollForResult(newTaskId);
    } catch (err) {
      console.error('Submission error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to submit prediction');
      setLoading(false);
      setPolling(false);
    }
  };

  const pollForResult = async (id) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = setInterval(async () => {
      try {
        console.log(`Polling attempt ${attempts + 1} for task ${id}`);
        
        const response = await axios.get(`${API_BASE_URL}/predictions/${id}`);
        const currentStatus = response.data.status;
        
        console.log('Current status:', currentStatus, response.data);
        setStatus(currentStatus);

        if (currentStatus === 'SUCCESS') {
          setResult(response.data.result);
          setLoading(false);
          setPolling(false);
          clearInterval(poll);
          console.log('Prediction complete:', response.data.result);
        } else if (currentStatus === 'FAILURE') {
          setError(response.data.error || 'Prediction failed');
          setLoading(false);
          setPolling(false);
          clearInterval(poll);
          console.error('Prediction failed:', response.data.error);
        }

        attempts++;
        if (attempts >= maxAttempts) {
          setError('Prediction timed out after 60 seconds');
          setLoading(false);
          setPolling(false);
          clearInterval(poll);
          console.error('Polling timed out');
        }
      } catch (err) {
        console.error('Polling error:', err);
        setError(err.response?.data?.detail || 'Failed to fetch prediction status');
        setLoading(false);
        setPolling(false);
        clearInterval(poll);
      }
    }, 1000);
  };

  const handleReset = () => {
    setSummary('');
    setDescription('');
    setTaskId(null);
    setStatus(null);
    setResult(null);
    setError(null);
    setLoading(false);
    setPolling(false);
  };

  return (
    <div className="prediction-container">
      <h2>Single Issue Prediction</h2>
      <p>Submit a single Jira issue for ADD classification</p>

      <form onSubmit={handleSubmit} className="prediction-form">
        <div className="form-group">
          <label htmlFor="summary">Issue Summary: *</label>
          <input
            id="summary"
            type="text"
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="e.g., Refactor authentication module"
            required
            disabled={loading}
            minLength={3}
          />
          <small>Brief title of the issue (minimum 3 characters)</small>
        </div>

        <div className="form-group">
          <label htmlFor="description">Issue Description: *</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., We need to refactor the authentication system to use OAuth2 instead of basic authentication for better security..."
            rows="8"
            required
            disabled={loading}
            minLength={10}
          />
          <small>Detailed description of the issue (minimum 10 characters)</small>
        </div>

        <div className="button-group">
          <button type="submit" disabled={loading || !summary.trim() || !description.trim()} className="btn-primary">
            {loading ? (polling ? 'Processing...' : 'Submitting...') : 'Submit Prediction'}
          </button>
          <button type="button" onClick={handleReset} className="btn-secondary" disabled={loading}>
            Reset
          </button>
        </div>
      </form>

      {taskId && (
        <div className="status-container">
          <p><strong>Task ID:</strong> <code>{taskId}</code></p>
          <p><strong>Status:</strong> <span className={`status-${status?.toLowerCase()}`}>{status}</span></p>
          {polling && <p className="polling-indicator">⏳ Checking for results...</p>}
        </div>
      )}

      {error && (
        <div className="error-message">
          <strong>❌ Error:</strong> {error}
          <p style={{marginTop: '0.5rem', fontSize: '0.9rem'}}>
            Please try again or contact support if the issue persists.
          </p>
        </div>
      )}

      {result && !error && (
        <div className="result-container success">
          <h3>✅ Prediction Result</h3>
          <div className="result-content">
            <div className="result-main">
              <p><strong>Classification:</strong> <span className={`classification ${result.prediction?.toLowerCase()}`}>{result.prediction || 'Unknown'}</span></p>
              <p><strong>Confidence:</strong> <span className="confidence">{result.confidence ? (result.confidence * 100).toFixed(2) + '%' : 'N/A'}</span></p>
            </div>
            
            {result.probabilities && (
              <div className="probabilities">
                <h4>Detailed Probabilities:</h4>
                <div className="prob-bars">
                  <div className="prob-item">
                    <span>ADD:</span>
                    <div className="prob-bar">
                      <div 
                        className="prob-fill add" 
                        style={{width: `${(result.probabilities.ADD * 100).toFixed(1)}%`}}
                      ></div>
                    </div>
                    <span>{(result.probabilities.ADD * 100).toFixed(1)}%</span>
                  </div>
                  <div className="prob-item">
                    <span>non-ADD:</span>
                    <div className="prob-bar">
                      <div 
                        className="prob-fill non-add" 
                        style={{width: `${(result.probabilities['non-ADD'] * 100).toFixed(1)}%`}}
                      ></div>
                    </div>
                    <span>{(result.probabilities['non-ADD'] * 100).toFixed(1)}%</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="info-box" style={{marginTop: '2rem'}}>
        <h4>How it works</h4>
        <ol>
          <li>Submit your issue summary and description</li>
          <li>The system queues your prediction task</li>
          <li>The ML model processes your request</li>
          <li>Results appear automatically (non-blocking)</li>
        </ol>
      </div>
    </div>
  );
}

export default SinglePrediction;