import React, { useState, useEffect } from 'react';
import './App.css';
import CaseStudy from './components/CaseStudy';
import ResponseForm from './components/ResponseForm';
import Results from './components/Results';
import MultiPartEvaluation from './components/MultiPartEvaluation';

function App() {
  const [evaluationType, setEvaluationType] = useState(null); // 'single' or 'multipart'
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [caseStudy, setCaseStudy] = useState('');
  const [isLoadingCase, setIsLoadingCase] = useState(false);

  // Function to fetch a new case study (for single evaluation)
  const fetchNewCaseStudy = async () => {
    setIsLoadingCase(true);
    try {
      const response = await fetch('http://localhost:8000/api/generate-case');
      if (response.ok) {
        const data = await response.json();
        setCaseStudy(data.caseStudy);
      } else {
        // Fallback to hardcoded case study if API fails
        setCaseStudy('Case Study: Unexplained Defects on Assembly Line 3. For the past week, the final quality check on Assembly Line 3 has seen a 15% increase in product defects. The defects are minor scratches on the product housing. This is causing rework delays and increasing material waste. Your task is to analyze this problem.');
      }
    } catch (error) {
      console.error('Error fetching case study:', error);
      // Fallback to hardcoded case study
      setCaseStudy('Case Study: Unexplained Defects on Assembly Line 3. For the past week, the final quality check on Assembly Line 3 has seen a 15% increase in product defects. The defects are minor scratches on the product housing. This is causing rework delays and increasing material waste. Your task is to analyze this problem.');
    } finally {
      setIsLoadingCase(false);
    }
  };

  const handleSubmit = async (analysisText) => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ analysisText }),
      });

      if (!response.ok) {
        throw new Error('Failed to evaluate analysis');
      }

      const evaluationResults = await response.json();
      setResults(evaluationResults);
    } catch (error) {
      console.error('Error submitting analysis:', error);
      alert('Error submitting analysis. Please make sure the backend server is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    setResults(null);
    setEvaluationType(null);
  };

  const handleSingleEvaluation = () => {
    setEvaluationType('single');
    fetchNewCaseStudy();
  };

  const handleMultiPartEvaluation = () => {
    setEvaluationType('multipart');
  };

  if (evaluationType === 'multipart') {
    return (
      <div className="App">
        <header className="App-header">
          <h1>Catalyst - Multi-Part Problem Analysis Assessment</h1>
          <button onClick={handleRetry} className="back-button">
            ← Back to Selection
          </button>
        </header>
        <main className="App-main">
          <MultiPartEvaluation />
        </main>
      </div>
    );
  }

  if (evaluationType === 'single') {
    return (
      <div className="App">
        <header className="App-header">
          <h1>Catalyst - Problem Analysis Skills Assessment</h1>
          <button onClick={handleRetry} className="back-button">
            ← Back to Selection
          </button>
        </header>
        <main className="App-main">
          {isLoading && (
            <div className="loading-message">
              <h3>Evaluating your analysis...</h3>
              <p>Please wait while our AI expert reviews your submission.</p>
            </div>
          )}
          
          {!isLoading && results && (
            <Results results={results} onRetry={handleRetry} />
          )}
          
          {!isLoading && !results && (
            <>
              <CaseStudy caseStudy={caseStudy} isLoading={isLoadingCase} />
              <ResponseForm onSubmit={handleSubmit} isLoading={isLoading} />
            </>
          )}
        </main>
      </div>
    );
  }

  // Evaluation type selection screen
  return (
    <div className="App">
      <header className="App-header">
        <h1>Catalyst - Manufacturing Problem Analysis Assessment</h1>
        <p className="subtitle">Choose your evaluation format</p>
      </header>
      <main className="App-main">
        <div className="evaluation-selection">
          <div className="evaluation-option">
            <div className="option-card">
              <h3>📝 Single Analysis</h3>
              <p>
                Provide a comprehensive analysis of a manufacturing problem in one submission. 
                Get evaluated on root cause identification and solution practicality.
              </p>
              <ul className="features-list">
                <li>Quick 10-15 minute assessment</li>
                <li>Open-ended response format</li>
                <li>2 evaluation criteria</li>
                <li>Immediate results</li>
              </ul>
              <button 
                onClick={handleSingleEvaluation}
                className="option-button single"
              >
                Start Single Analysis
              </button>
            </div>
          </div>

          <div className="evaluation-option">
            <div className="option-card featured">
              <h3>🎯 Multi-Part Assessment</h3>
              <p>
                Complete a comprehensive 4-part evaluation that tests different aspects 
                of your problem-solving methodology step by step.
              </p>
              <ul className="features-list">
                <li>Thorough 30-45 minute assessment</li>
                <li>4 structured parts with guided questions</li>
                <li>12 specialized evaluation criteria</li>
                <li>Detailed performance analytics</li>
                <li>Progressive difficulty</li>
              </ul>
              <button 
                onClick={handleMultiPartEvaluation}
                className="option-button multipart"
              >
                Start Multi-Part Assessment
              </button>
              <div className="recommended-badge">Recommended</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
