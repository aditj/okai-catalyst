import React, { useState } from 'react';
import './App.css';
import MultiPartEvaluation from './components/MultiPartEvaluation';

function App() {
  const [evaluationType, setEvaluationType] = useState(null); // only 'multipart' now

  const handleRetry = () => {
    setEvaluationType(null);
  };

  const handleMultiPartEvaluation = () => {
    setEvaluationType('multipart');
  };

  if (evaluationType === 'multipart') {
    return (
      <div className="App">
        
        <header className="App-header">
        <img
          src={process.env.PUBLIC_URL + '/logo512.png'}
          alt="Catalyst Logo"
          className="header-logo"
        />
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

  // Evaluation type selection screen
  return (
    <div className="App">
      <header className="App-header">
        {/* Application logo */}
        <img
          src={process.env.PUBLIC_URL + '/logo512.png'}
          alt="Catalyst Logo"
          className="header-logo"
        />
        <h1>Catalyst - Manufacturing Problem Analysis Assessment</h1>
        <p className="subtitle">Choose your evaluation format</p>
      </header>
      <main className="App-main">
        <div className="evaluation-selection">
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
