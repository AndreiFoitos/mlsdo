import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = '/api';

function LabelSubmission() {
  const [summary, setSummary] = useState('');
  const [description, setDescription] = useState('');
  const [label, setLabel] = useState('ADD');
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/issues/labeled`, {
        summary,
        description,
        label
      });

      setSuccess(response.data.message);
      setSummary('');
      setDescription('');
      setLabel('ADD');
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit labeled issue');
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSummary('');
    setDescription('');
    setLabel('ADD');
    setSuccess(null);
    setError(null);
  };

  return (
    <div className="prediction-container">
      <h2>Submit Labeled Data (Bonus Feature)</h2>
      <p>Help improve the model by submitting labeled examples</p>

      <form onSubmit={handleSubmit} className="prediction-form">
        <div className="form-group">
          <label htmlFor="summary">Issue Summary:</label>
          <input
            id="summary"
            type="text"
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
            placeholder="Enter issue summary..."
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">Issue Description:</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Enter detailed description..."
            rows="6"
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="label">Label:</label>
          <select
            id="label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            disabled={loading}
          >
            <option value="ADD">ADD (Architectural Design Decision)</option>
            <option value="non-ADD">non-ADD (Not an Architectural Decision)</option>
          </select>
        </div>

        <div className="button-group">
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Submitting...' : 'Submit Labeled Issue'}
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

      {success && (
        <div className="success-message">
          <strong>✓ Success!</strong> {success}
          <p>Thank you for contributing to model improvement!</p>
        </div>
      )}

      <div className="info-box">
        <h4>💡 About Labeled Data</h4>
        <p>
          Submitting labeled examples helps improve the model's accuracy over time.
          Your contributions will be used in future model training iterations.
        </p>
        <ul>
          <li><strong>ADD:</strong> Issues that involve architectural design decisions</li>
          <li><strong>non-ADD:</strong> Regular issues that don't involve architectural decisions</li>
        </ul>
      </div>
    </div>
  );
}

export default LabelSubmission;