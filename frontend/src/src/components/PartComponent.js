import React, { useState } from 'react';
import './PartComponent.css';
import AudioRecorder from './AudioRecorder';

function PartComponent({ part, onSubmit, isSubmitting, evaluation }) {
  const [responses, setResponses] = useState({});
  const [audioData, setAudioData] = useState(null);

  const handleResponseChange = (questionId, value) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const handleAudioData = (base64Data) => {
    setAudioData(base64Data);
    // For audio questions, we set a placeholder response
    if (base64Data) {
      setResponses(prev => ({
        ...prev,
        'q5_verbal': 'Audio recording submitted'
      }));
    } else {
      setResponses(prev => {
        const newResponses = { ...prev };
        delete newResponses['q5_verbal'];
        return newResponses;
      });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Special validation for Part 5 (audio)
    if (part.id === 5) {
      if (!audioData) {
        alert('Please record your 2-minute explanation before submitting.');
        return;
      }
      // Submit with audio data
      onSubmit(part.id, responses, audioData);
      return;
    }
    
    // Add placeholder texts for empty responses
    const processedResponses = { ...responses };
    part.questions.forEach(question => {
      if (!processedResponses[question.id] || processedResponses[question.id].trim() === '') {
        processedResponses[question.id] = `[No response provided for: ${question.question.substring(0, 100)}...]`;
      }
    });

    onSubmit(part.id, processedResponses);
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
          
          {evaluation.transcription && (
            <div className="transcription-section">
              <h5>Audio Transcription</h5>
              <div className="transcription-content">
                <p>{evaluation.transcription}</p>
              </div>
            </div>
          )}
          
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
            
            {question.type === 'audio' ? (
              <div className="audio-question">
                <AudioRecorder 
                  onAudioData={handleAudioData}
                  disabled={isSubmitting}
                />
                {question.instructions && (
                  <div className="question-instructions">
                    <p><strong>Instructions:</strong> {question.instructions}</p>
                  </div>
                )}
              </div>
            ) : (
              <textarea
                className="question-textarea"
                placeholder="Enter your detailed response here... (Optional: You can skip questions and continue if needed)"
                value={responses[question.id] || ''}
                onChange={(e) => handleResponseChange(question.id, e.target.value)}
                rows="4"
                disabled={isSubmitting}
              />
            )}
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

        <div className="submission-info">
          <p><strong>Note:</strong> All questions are optional. If you skip any questions, placeholder text will be added automatically. You can always return to provide more detailed responses.</p>
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