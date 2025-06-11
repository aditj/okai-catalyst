import React from 'react';
import './Results.css';

function Results({ results, onRetry }) {
  const { rootCauseScore, solutionScore, feedback } = results;

  const getScoreColor = (score) => {
    if (score >= 8) return '#28a745'; // Green
    if (score >= 6) return '#ffc107'; // Yellow
    return '#dc3545'; // Red
  };

  const getScoreLabel = (score) => {
    if (score >= 8) return 'Excellent';
    if (score >= 6) return 'Good';
    if (score >= 4) return 'Fair';
    return 'Needs Improvement';
  };

  return (
    <div className="results">
      <h2>Analysis Evaluation Results</h2>
      
      <div className="scores-container">
        <div className="score-card">
          <h3>Root Cause Identification</h3>
          <div 
            className="score-circle"
            style={{ backgroundColor: getScoreColor(rootCauseScore) }}
          >
            <span className="score-number">{rootCauseScore}</span>
            <span className="score-max">/10</span>
          </div>
          <p className="score-label">{getScoreLabel(rootCauseScore)}</p>
        </div>

        <div className="score-card">
          <h3>Solution Practicality</h3>
          <div 
            className="score-circle"
            style={{ backgroundColor: getScoreColor(solutionScore) }}
          >
            <span className="score-number">{solutionScore}</span>
            <span className="score-max">/10</span>
          </div>
          <p className="score-label">{getScoreLabel(solutionScore)}</p>
        </div>
      </div>

      <div className="feedback-section">
        <h3>Expert Feedback</h3>
        <div className="feedback-content">
          <p>{feedback}</p>
        </div>
      </div>

      <div className="actions">
        <button onClick={onRetry} className="retry-button">
          Try Another Case Study
        </button>
      </div>
    </div>
  );
}

export default Results; 