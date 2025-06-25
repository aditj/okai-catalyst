import React, { useState, useEffect } from 'react';
import './FinalResults.css';

// Base URL for backend API
const API_BASE_URL = 'https://okai-catalyst.onrender.com';
// const API_BASE_URL = 'http://localhost:5002';

function FinalResults({ sessionId, partEvaluations, onRetry }) {
  const [finalEvaluation, setFinalEvaluation] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchFinalEvaluation();
  }, [sessionId]);

  const fetchFinalEvaluation = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/final-evaluation/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        console.log('Final evaluation data:', data); // Debug log
        setFinalEvaluation(data);
      } else {
        const errorText = await response.text();
        console.error('Response error:', response.status, errorText);
        throw new Error(`Failed to fetch final evaluation: ${response.status} - ${errorText}`);
      }
    } catch (error) {
      console.error('Error fetching final evaluation:', error);
      alert(`Error loading final evaluation: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 8) return '#28a745'; // Green
    if (score >= 6) return '#ffc107'; // Yellow
    if (score >= 4) return '#fd7e14'; // Orange
    return '#dc3545'; // Red
  };

  const getPerformanceColor = (performance) => {
    switch(performance.toLowerCase()) {
      case 'excellent': return '#28a745';
      case 'good': return '#17a2b8';
      case 'satisfactory': return '#ffc107';
      default: return '#dc3545';
    }
  };

  const getPriorityColor = (priority) => {
    switch(priority.toLowerCase()) {
      case 'high': return '#dc3545';
      case 'medium': return '#ffc107';
      case 'low': return '#28a745';
      default: return '#6c757d';
    }
  };

  const getPriorityIcon = (priority) => {
    switch(priority.toLowerCase()) {
      case 'high': return '🔥';
      case 'medium': return '⚡';
      case 'low': return '📚';
      default: return '📋';
    }
  };

  if (isLoading) {
    return (
      <div className="final-results-loading">
        <h2>Calculating Final Results...</h2>
        <p>Analyzing your performance across all parts...</p>
      </div>
    );
  }

  if (!finalEvaluation) {
    return (
      <div className="final-results-error">
        <h2>Error Loading Results</h2>
        <button onClick={fetchFinalEvaluation} className="retry-button">
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="final-results">
      <div className="results-header">
        <h1>🎉 Evaluation Complete!</h1>
        <div 
          className="overall-performance"
          style={{ backgroundColor: getPerformanceColor(finalEvaluation.overallPerformance) }}
        >
          {finalEvaluation.overallPerformance}
        </div>
      </div>

      <div className="overall-scores-section">
        <h2>Overall Performance Scores</h2>
        <div className="overall-scores-grid">
          {Object.entries(finalEvaluation.overallScores).map(([category, score]) => (
            <div key={category} className="overall-score-card">
              <h3>{category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h3>
              <div 
                className="score-circle"
                style={{ backgroundColor: getScoreColor(score) }}
              >
                <span className="score-number">{score}</span>
                <span className="score-max">/10</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="detailed-feedback-section">
        <h2>Expert Feedback</h2>
        <div className="detailed-feedback">
          <p>{finalEvaluation.detailedFeedback}</p>
        </div>
      </div>

      {finalEvaluation.toolRecommendations && Object.keys(finalEvaluation.toolRecommendations).length > 0 && (
        <div className="tool-recommendations-section">
          <h2>🛠️ Recommended Quality Management Tools</h2>
          <div className="tool-recommendations-intro">
            <p>Based on your performance analysis, here are specific quality management tools that can help strengthen your skills:</p>
          </div>
          <div className="tool-recommendations-grid">
            {Object.entries(finalEvaluation.toolRecommendations).map(([toolName, details]) => (
              <div key={toolName} className="tool-recommendation-card">
                <div className="tool-header">
                  <h3>{toolName}</h3>
                  <div 
                    className="priority-badge"
                    style={{ backgroundColor: getPriorityColor(details.priority) }}
                  >
                    <span className="priority-icon">{getPriorityIcon(details.priority)}</span>
                    <span className="priority-text">{details.priority} Priority</span>
                  </div>
                </div>
                <div className="tool-content">
                  <div className="tool-reason">
                    <h4>Why This Tool?</h4>
                    <p>{details.reason}</p>
                  </div>
                  <div className="tool-benefit">
                    <h4>What You'll Gain</h4>
                    <p>{details.specific_benefit}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="learning-path-note">
            <div className="learning-path-content">
              <h4>📈 Your Learning Path</h4>
              <p>Start with <strong>High Priority</strong> tools first, as these address your most significant improvement areas. These tools are industry-standard methods used by quality professionals worldwide.</p>
            </div>
          </div>
        </div>
      )}

      <div className="part-by-part-section">
        <h2>Part-by-Part Breakdown</h2>
        <div className="parts-breakdown">
          {finalEvaluation.partScores.map((partScore) => (
            <div key={partScore.partId} className="part-summary">
              <h3>Part {partScore.partId}: {partScore.title}</h3>
              <div className="part-scores">
                {Object.entries(partScore.scores).map(([rubric, score]) => (
                  <div key={rubric} className="part-score-item">
                    <span className="rubric-name">
                      {rubric.replace(/_/g, ' ')}
                    </span>
                    <span 
                      className="score-badge"
                      style={{ backgroundColor: getScoreColor(score) }}
                    >
                      {score}/10
                    </span>
                  </div>
                ))}
              </div>
              <div className="part-feedback">
                <p>{partScore.feedback}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="actions-section">
        <button onClick={onRetry} className="new-evaluation-button">
          Start New Evaluation
        </button>
        <button 
          onClick={() => window.print()} 
          className="print-results-button"
        >
          Print Results
        </button>
      </div>
    </div>
  );
}

export default FinalResults; 