import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = '/api';

function BatchPrediction() {
  const [issues, setIssues] = useState([
    { id: 1, summary: '', description: '' },
    { id: 2, summary: '', description: '' }
  ]);
  const [taskIds, setTaskIds] = useState([]);
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [polling, setPolling] = useState(false);
  const [completedCount, setCompletedCount] = useState(0);

  const handleAddIssue = () => {
    const newId = Math.max(...issues.map(i => i.id)) + 1;
    setIssues([...issues, { id: newId, summary: '', description: '' }]);
  };

  const handleRemoveIssue = (id) => {
    if (issues.length > 1) {
      setIssues(issues.filter(issue => issue.id !== id));
    }
  };

  const handleIssueChange = (id, field, value) => {
    setIssues(issues.map(issue => 
      issue.id === id ? { ...issue, [field]: value } : issue
    ));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults({});
    setCompletedCount(0);
    setPolling(false);

    const validIssues = issues.filter(i => i.summary.trim() && i.description.trim());
    if (validIssues.length === 0) {
      setError('Please fill in at least one issue with both summary and description');
      setLoading(false);
      return;
    }

    try {
      console.log('Submitting batch prediction:', validIssues);
      
      const response = await axios.post(`${API_BASE_URL}/predictions/batch`, {
        issues: validIssues.map(i => ({
          summary: i.summary.trim(),
          description: i.description.trim()
        }))
      });

      console.log('Batch submitted:', response.data);
      
      const ids = response.data.task_ids;
      setTaskIds(ids);
      setPolling(true);


      const initialResults = {};
      ids.forEach((id, idx) => {
        initialResults[id] = {
          status: 'PENDING',
          issueIndex: idx,
          summary: validIssues[idx].summary
        };
      });
      setResults(initialResults);

      pollForBatchResults(ids);
    } catch (err) {
      console.error('Batch submission error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to submit batch prediction');
      setLoading(false);
      setPolling(false);
    }
  };

  const pollForBatchResults = async (ids) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = setInterval(async () => {
      try {
        console.log(`Batch polling attempt ${attempts + 1}`);
        
        const statusPromises = ids.map(id => 
          axios.get(`${API_BASE_URL}/predictions/${id}`)
            .catch(err => ({ data: { task_id: id, status: 'ERROR', error: err.message } }))
        );
        
        const responses = await Promise.all(statusPromises);
        
        let completed = 0;
        const newResults = {};

        responses.forEach((response, index) => {
          const taskData = response.data;
          const taskId = ids[index];
          
          newResults[taskId] = {
            ...results[taskId],
            status: taskData.status,
            result: taskData.result,
            error: taskData.error
          };

          if (taskData.status === 'SUCCESS' || taskData.status === 'FAILURE' || taskData.status === 'ERROR') {
            completed++;
          }
        });

        setResults(newResults);
        setCompletedCount(completed);

        if (completed === ids.length) {
          setLoading(false);
          setPolling(false);
          clearInterval(poll);
          console.log('All batch predictions complete');
        }

        attempts++;
        if (attempts >= maxAttempts) {
          setError('Some predictions timed out after 60 seconds');
          setLoading(false);
          setPolling(false);
          clearInterval(poll);
        }
      } catch (err) {
        console.error('Batch polling error:', err);
        setError('Failed to fetch batch prediction status');
        setLoading(false);
        setPolling(false);
        clearInterval(poll);
      }
    }, 2000);
  };

  const handleReset = () => {
    setIssues([
      { id: 1, summary: '', description: '' },
      { id: 2, summary: '', description: '' }
    ]);
    setTaskIds([]);
    setResults({});
    setError(null);
    setLoading(false);
    setPolling(false);
    setCompletedCount(0);
  };

  const allIssuesFilled = issues.every(i => i.summary.trim() && i.description.trim());
  const someIssuesFilled = issues.some(i => i.summary.trim() && i.description.trim());

  return (
    <div className="prediction-container">
      <h2>Batch Issue Prediction</h2>
      <p>Submit multiple Jira issues for ADD classification at once</p>

      <form onSubmit={handleSubmit} className="batch-form">
        {issues.map((issue, index) => (
          <div key={issue.id} className="batch-issue-item">
            <div className="issue-header">
              <h4>Issue #{index + 1}</h4>
              {issues.length > 1 && (
                <button
                  type="button"
                  onClick={() => handleRemoveIssue(issue.id)}
                  className="btn-remove"
                  disabled={loading}
                >
                  ✕ Remove
                </button>
              )}
            </div>

            <div className="form-group">
              <label>Summary: *</label>
              <input
                type="text"
                value={issue.summary}
                onChange={(e) => handleIssueChange(issue.id, 'summary', e.target.value)}
                placeholder="e.g., Implement caching layer"
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>Description: *</label>
              <textarea
                value={issue.description}
                onChange={(e) => handleIssueChange(issue.id, 'description', e.target.value)}
                placeholder="e.g., Add Redis caching to improve API response times..."
                rows="4"
                required
                disabled={loading}
              />
            </div>
          </div>
        ))}

        <button 
          type="button" 
          onClick={handleAddIssue} 
          className="btn-add"
          disabled={loading}
        >
          ➕ Add Another Issue
        </button>

        <div className="button-group">
          <button 
            type="submit" 
            disabled={loading || !someIssuesFilled} 
            className="btn-primary"
          >
            {loading ? 'Processing...' : `Submit ${issues.length} Issue${issues.length > 1 ? 's' : ''}`}
          </button>
          <button type="button" onClick={handleReset} className="btn-secondary" disabled={loading}>
            Reset All
          </button>
        </div>

        {!allIssuesFilled && someIssuesFilled && !loading && (
          <p className="warning-text">Only issues with both summary and description will be submitted</p>
        )}
      </form>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {taskIds.length > 0 && (
        <div className="batch-status">
          <h3>Batch Processing Status</h3>
          <p>
            <strong>{completedCount} / {taskIds.length}</strong> predictions complete
            {polling && <span className="polling-indicator"> ⏳ Processing...</span>}
          </p>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{width: `${(completedCount / taskIds.length) * 100}%`}}
            ></div>
          </div>
        </div>
      )}

      {Object.keys(results).length > 0 && (
        <div className="results-container">
          <h3>Batch Results</h3>
          <div className="batch-results-grid">
            {Object.entries(results).map(([taskId, data], index) => (
              <div key={taskId} className={`batch-result-card status-${data.status?.toLowerCase()}`}>
                <div className="card-header">
                  <h4>Issue #{data.issueIndex + 1}</h4>
                  <span className={`status-badge ${data.status?.toLowerCase()}`}>
                    {data.status}
                  </span>
                </div>
                
                <p className="issue-summary">{data.summary}</p>
                
                <p className="task-id"><small>Task: {taskId.substring(0, 8)}...</small></p>
                
                {data.result && (
                  <div className="result-details">
                    <p><strong>Prediction:</strong> <span className={`prediction-label ${data.result.label?.toLowerCase()}`}>{data.result.label}</span></p>
                    <p><strong>Confidence:</strong> {(data.result.probability * 100).toFixed(1)}%</p>
                    {data.result.types && (
                      <div className="decision-types">
                        <small>
                          Types: {data.result.types.existence ? 'Existence ' : ''}
                          {data.result.types.executive ? 'Executive ' : ''}
                          {data.result.types.property ? 'Property' : ''}
                        </small>
                      </div>
                    )}
                  </div>
                )}
                
                {data.error && (
                  <p className="error-text">{data.error}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="info-box" style={{marginTop: '2rem'}}>
        <h4>Batch Processing Tips</h4>
        <ul>
          <li>Add up to 10 issues at once for efficient processing</li>
          <li>Each issue is processed independently and asynchronously</li>
          <li>Results appear as soon as each prediction completes</li>
          <li>You can continue working while predictions are being processed</li>
        </ul>
      </div>
    </div>
  );
}

export default BatchPrediction;