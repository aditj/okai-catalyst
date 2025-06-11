import React, { useState } from 'react';
import './PartComponent.css';

function PartComponent({ part, onSubmit, isSubmitting, evaluation }) {
  const [responses, setResponses] = useState({});

  const handleResponseChange = (questionId, value) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Check if all questions are answered
    const unansweredQuestions = part.questions.filter(
      q => !responses[q.id] || responses[q.id].trim() === ''
    );

    if (unansweredQuestions.length > 0) {
      alert(`Please answer all questions before submitting. Missing: ${unansweredQuestions.map(q => q.question.substring(0, 50) + '...').join(', ')}`);
      return;
    }

    onSubmit(part.id, responses);
  };

  if (evaluation && !evaluation.canProceed) {
    return (
      <div className="part-component evaluation-feedback">
        <div className="part-header">
          <h3>Part {part.id}: {part.title}</h3>
          <p className="part-description">{part.description}</p>
        </div>

        <div className="evaluation-results">
          <h4>Evaluation Results</h4>
          <div className="scores-grid">
            {Object.entries(evaluation.scores).map(([rubric, score]) => (
              <div key={rubric} className="score-item">
                <span className="rubric-name">{rubric.replace(/_/g, ' ')}</span>
                <span className={`score ${score >= 7 ? 'good' : score >= 5 ? 'fair' : 'poor'}`}>
                  {score}/10
                </span>
              </div>
            ))}
          </div>
          
          <div className="feedback">
            <h5>Feedback</h5>
            <p>{evaluation.feedback}</p>
          </div>

          <div className="retry-message">
            <p><strong>You need to improve your responses before proceeding to the next part.</strong></p>
            <button 
              onClick={() => window.location.reload()} 
              className="retry-part-button"
            >
              Start Over
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="part-component">
      <div className="part-header">
        <h3>Part {part.id}: {part.title}</h3>
        <p className="part-description">{part.description}</p>
      </div>

      <form onSubmit={handleSubmit} className="part-form">
        {part.questions.map((question, index) => (
          <div key={question.id} className="question-group">
            <label className="question-label">
              <span className="question-number">Question {index + 1}:</span>
              <span className="question-text">{question.question}</span>
            </label>
            <textarea
              className="question-textarea"
              placeholder="Enter your detailed response here..."
              value={responses[question.id] || ''}
              onChange={(e) => handleResponseChange(question.id, e.target.value)}
              rows="4"
              disabled={isSubmitting}
            />
          </div>
        ))}

        <div className="rubrics-info">
          <h4>Evaluation Criteria</h4>
          <div className="rubrics-list">
            {Object.entries(part.rubrics).map(([key, description]) => (
              <div key={key} className="rubric-item">
                <strong>{key.replace(/_/g, ' ')}:</strong> {description}
              </div>
            ))}
          </div>
        </div>

        <button 
          type="submit" 
          className="submit-part-button"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Evaluating...' : `Submit Part ${part.id}`}
        </button>
      </form>
    </div>
  );
}

export default PartComponent; 