import React, { useState } from 'react';
import './ResponseForm.css';

function ResponseForm({ onSubmit, isLoading }) {
  const [analysisText, setAnalysisText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!analysisText.trim()) {
      alert('Please enter your analysis before submitting.');
      return;
    }

    onSubmit(analysisText);
    setAnalysisText(''); // Clear the form after submission
  };

  return (
    <div className="response-form">
      <h3>Submit Your Analysis</h3>
      <form onSubmit={handleSubmit}>
        <textarea
          className="analysis-textarea"
          placeholder="Type your analysis here..."
          value={analysisText}
          onChange={(e) => setAnalysisText(e.target.value)}
          rows="10"
          cols="50"
        />
        <br />
        <button type="submit" className="submit-button" disabled={isLoading}>
          {isLoading ? 'Evaluating...' : 'Submit Analysis'}
        </button>
      </form>
    </div>
  );
}

export default ResponseForm; 