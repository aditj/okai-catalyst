import React, { useState, useEffect } from 'react';
import './MultiPartEvaluation.css';
import PartComponent from './PartComponent';
import FinalResults from './FinalResults';

// Helper function to format case study content for better readability
const formatCaseStudyContent = (content) => {
  if (!content) return null;
  
  // Split content into sentences for better formatting
  const sentences = content.split(/(?<=[.!?])\s+/);
  const paragraphs = [];
  let currentParagraph = [];
  
  sentences.forEach((sentence, index) => {
    currentParagraph.push(sentence);
    
    // Create a new paragraph every 3-4 sentences or at logical breaks
    if (currentParagraph.length >= 3 || 
        sentence.includes('AeroGlide Manufacturing') ||
        sentence.includes('Production efficiency') ||
        sentence.includes('Process Engineering') ||
        sentence.includes('Shop floor workers') ||
        sentence.includes('Your task is to')) {
      
      paragraphs.push(currentParagraph.join(' '));
      currentParagraph = [];
    }
  });
  
  // Add any remaining sentences
  if (currentParagraph.length > 0) {
    paragraphs.push(currentParagraph.join(' '));
  }
  
  return paragraphs.map((paragraph, index) => (
    <p key={index} style={{ marginBottom: index < paragraphs.length - 1 ? '16px' : '0' }}>
      {paragraph}
    </p>
  ));
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
      const response = await fetch('http://localhost:8000/api/generate-multipart-case');
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

  const handlePartSubmit = async (partId, responses) => {
    setIsSubmitting(true);
    try {
      const response = await fetch('http://localhost:8000/api/submit-part', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          partId,
          responses,
          sessionId: sessionData.sessionId
        }),
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
        if (partId < 4) {
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
      <div className="case-study-section">
        <h2>Manufacturing Case Study</h2>
        <div className="case-study-content">
          {formatCaseStudyContent(sessionData.caseStudy)}
        </div>
      </div>

      <div className="progress-section">
        <h3>Evaluation Progress</h3>
        <div className="progress-bar">
          {[1, 2, 3, 4].map(partNum => (
            <div 
              key={partNum}
              className={`progress-step ${
                completedParts.includes(partNum) ? 'completed' : 
                partNum === currentPart ? 'current' : 'pending'
              }`}
            >
              <span className="step-number">{partNum}</span>
              <span className="step-title">
                {sessionData.parts.find(p => p.id === partNum)?.title}
              </span>
            </div>
          ))}
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