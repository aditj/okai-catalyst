import React from 'react';
import './CaseStudy.css';

function CaseStudy({ caseStudy, isLoading }) {
  if (isLoading) {
    return (
      <div className="case-study">
        <div className="case-study-loading">
          <h2>Loading Case Study...</h2>
          <p>Generating a new manufacturing scenario for you to analyze.</p>
        </div>
      </div>
    );
  }

  // Extract title and content from the case study text
  const lines = caseStudy.split('.');
  const title = lines[0] || 'Manufacturing Case Study';
  const content = lines.slice(1).join('.').trim();

  return (
    <div className="case-study">
      <h2 className="case-study-title">{title}</h2>
      <div className="case-study-content">
        <p>{content || caseStudy}</p>
      </div>
    </div>
  );
}

export default CaseStudy; 