import React, { useState, useEffect } from 'react';
import './MultiPartEvaluation.css';
import PartComponent from './PartComponent';
import FinalResults from './FinalResults';
const API_BASE_URL = 'https://okai-catalyst.onrender.com';
// const API_BASE_URL = 'http://localhost:4000';
// Base URL for backend API


// Helper function to format case study content as a markdown block
const formatCaseStudyContent = (content) => {
  if (!content) return null;
  
  return (
    <pre className="case-study-markdown">
      {content}
    </pre>
  );
};

function MultiPartEvaluation() {
  const [sessionData, setSessionData] = useState(null);
  const [currentPart, setCurrentPart] = useState(1);
  const [completedParts, setCompletedParts] = useState([]);
  const [partEvaluations, setPartEvaluations] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showFinalResults, setShowFinalResults] = useState(false);

  // Fetch case study and initialize session
  useEffect(() => {
    fetchCaseStudy();
  }, []);

  const fetchCaseStudy = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/generate-multipart-case`);
      if (response.ok) {
        const data = await response.json();
        setSessionData(data);
      } else {
        throw new Error('Failed to fetch case study');
      }
    } catch (error) {
      console.error('Error fetching case study:', error);
      alert('Error loading case study. Please make sure the backend server is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePartSubmit = async (partId, responses, audioData = null) => {
    setIsSubmitting(true);
    try {
      const requestBody = {
        partId,
        responses,
        sessionId: sessionData.sessionId
      };

      // Add audio data for Part 5
      if (audioData) {
        requestBody.audioData = audioData;
      }

      const response = await fetch(`${API_BASE_URL}/api/submit-part`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error('Failed to submit part');
      }

      const evaluation = await response.json();
      
      // Store the evaluation
      setPartEvaluations(prev => ({
        ...prev,
        [partId]: evaluation
      }));

      // Add to completed parts if can proceed
      if (evaluation.canProceed) {
        setCompletedParts(prev => [...prev, partId]);
        
        // Move to next part or show final results
        if (partId < 5) {
          setCurrentPart(partId + 1);
        } else {
          // All parts completed, show final results
          setShowFinalResults(true);
        }
      }

    } catch (error) {
      console.error('Error submitting part:', error);
      alert('Error submitting part. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetry = () => {
    setSessionData(null);
    setCurrentPart(1);
    setCompletedParts([]);
    setPartEvaluations({});
    setShowFinalResults(false);
    fetchCaseStudy();
  };

  if (isLoading) {
    return (
      <div className="multi-part-loading">
        <h2>Loading Case Study...</h2>
        <p>Generating a comprehensive manufacturing scenario for multi-part analysis.</p>
      </div>
    );
  }

  if (!sessionData) {
    return (
      <div className="multi-part-error">
        <h2>Error Loading Case Study</h2>
        <button onClick={fetchCaseStudy} className="retry-button">
          Try Again
        </button>
      </div>
    );
  }

  if (showFinalResults) {
    return (
      <FinalResults 
        sessionId={sessionData.sessionId}
        partEvaluations={partEvaluations}
        onRetry={handleRetry}
      />
    );
  }

  return (
    <div className="multi-part-evaluation">
      <div className="progress-section">
        <h3>Evaluation Progress</h3>
        <div className="progress-bar">
          {[1, 2, 3, 4, 5].map(partNum => (
            <div 
              key={partNum}
              className={`progress-step ${
                completedParts.includes(partNum) ? 'completed' : 
                partNum === currentPart ? 'current' : 'pending'
              }`}
            >
              <span className="step-number">{partNum}</span>
              <span className="step-title">
                {sessionData.parts.find(p => p.id === partNum)?.title || 
                 (partNum === 5 ? 'Verbal Explanation' : `Part ${partNum}`)}
              </span>
            </div>
          ))}
        </div>
        <div className="progress-info">
          <p>
            <strong>Estimated Time:</strong> {sessionData.estimatedTime || '35-50 minutes'} 
            <span className="progress-current">
              {' '} • Currently on Part {currentPart} of 5
            </span>
          </p>
        </div>
      </div>
      
      <div className="case-study-section">
        <h2>Manufacturing Case Study</h2>
        <div className="case-study-content">
          {formatCaseStudyContent(sessionData.caseStudy)}
        </div>
      </div>

      <div className="current-part-section">
        {sessionData.parts.map(part => (
          part.id === currentPart && (
            <PartComponent
              key={part.id}
              part={part}
              onSubmit={handlePartSubmit}
              isSubmitting={isSubmitting}
              evaluation={partEvaluations[part.id]}
            />
          )
        ))}
      </div>
    </div>
  );
}

export default MultiPartEvaluation; 