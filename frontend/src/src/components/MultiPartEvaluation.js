import React, { useState, useEffect } from 'react';
import './MultiPartEvaluation.css';
import PartComponent from './PartComponent';
import FinalResults from './FinalResults';
const API_BASE_URL = 'https://okai-catalyst.onrender.com';
// const API_BASE_URL = 'http://localhost:5002';
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
  const [demoMode, setDemoMode] = useState(null);
  const [showLoadingOverlay, setShowLoadingOverlay] = useState(false);

  // Demo data for good and bad responses
  const demoData = {
    good: {
      1: {
        q1_data: "I would collect the following key quantitative metrics: 1) Defect rate by assembly station (PPM) to identify which stations have highest failure rates, 2) First-pass yield percentage at each inspection point to pinpoint where defects are caught, 3) Process capability indices (Cpk) for critical dimensions to assess process stability, 4) Supplier quality metrics including incoming inspection data and supplier scorecards to evaluate the new supplier's performance, 5) Machine performance data including cycle times, downtime, and calibration records for the upgraded software machines. These metrics are essential because they provide objective data to identify patterns, isolate problem sources, and measure improvement effectiveness.",
        q1_stakeholders: "Key people to interview: 1) Production supervisors from all three shifts to understand shift-specific patterns and operational differences, 2) Quality inspectors to gather insights on defect characteristics and trends they've observed, 3) Maintenance technicians to assess machine performance and any issues with the upgraded software, 4) Incoming inspection team to evaluate new supplier quality and any changes in component characteristics, 5) Process engineers to understand recent process changes and their potential impact, 6) Customer service representatives to understand specific customer complaints and failure modes. Each provides unique operational insights that data alone cannot reveal.",
        q1_observations: "My observation plan would include: 1) Conduct gemba walks during all three shifts (minimum 2 hours per shift) to observe actual work practices and identify variations between shifts, 2) Shadow quality inspectors during their inspection processes to understand how defects are identified and categorized, 3) Observe the four upgraded assembly stations during operation to identify any software-related issues or operator difficulties, 4) Monitor incoming inspection processes for the new supplier components to assess quality and handling procedures, 5) Document environmental conditions (temperature, humidity) that might affect component or assembly quality. Timing would focus on peak production hours and shift changes when quality issues are most likely to occur."
      },
      2: {
        q2_causes: "Using the 5M framework, potential root causes include: MAN - Insufficient training on upgraded machine software leading to improper setup or operation; different skill levels across shifts causing inconsistent quality. MACHINE - Software bugs or calibration issues in the four upgraded assembly stations; inadequate integration between new software and existing hardware. MATERIAL - Quality issues with the new supplier's components including dimensional variations or material property changes; inadequate incoming inspection protocols for new supplier. METHOD - Inadequate process validation after software upgrades; lack of updated work instructions reflecting software changes; insufficient process controls for new supplier integration. ENVIRONMENT - Environmental factors affecting component stability or assembly precision; inadequate storage conditions for new supplier components.",
        q2_method: "I would use a combination of Fishbone Diagram and 5 Whys analysis. The Fishbone Diagram is ideal for this multi-faceted problem because it systematically categorizes potential causes and helps visualize relationships between different factors. I'd start with the main problem (quality defects) and branch out into the 5Ms, then use 5 Whys for each major branch to drill down to root causes. For example, for 'Machine' branch: Why are defects occurring at assembly stations? → Software integration issues. Why software integration issues? → Inadequate testing during upgrade. This combination ensures both breadth and depth in analysis.",
        q2_validation: "To validate root causes, I would: 1) Conduct statistical analysis comparing defect rates before/after software upgrade and supplier change to establish correlation, 2) Run designed experiments isolating variables (old vs new supplier components, upgraded vs non-upgraded stations), 3) Perform capability studies on the four upgraded machines versus non-upgraded ones, 4) Implement temporary process changes to test hypotheses (e.g., enhanced incoming inspection for new supplier), 5) Use control charts to monitor process stability during testing. Evidence would include statistical significance in defect rate differences, process capability improvements when variables are controlled, and sustained improvement when corrective actions are implemented."
      },
      3: {
        q3_solutions: "Solution 1: Comprehensive software re-validation and operator retraining (High effort) - Addresses potential software integration issues and operator competency gaps. Solution 2: Enhanced incoming inspection protocol for new supplier with statistical sampling (Medium effort) - Directly addresses potential component quality issues from supplier change. Solution 3: Implementation of poka-yoke devices at critical assembly points (Medium effort) - Prevents human error and ensures consistent assembly regardless of operator skill level. Solution 4: Shift-specific process standardization with visual management (Low effort) - Addresses variations between shifts through standardized work procedures and visual controls.",
        q3_implementation: "For enhanced incoming inspection protocol: Week 1-2: Develop detailed inspection criteria and statistical sampling plans based on critical-to-quality characteristics. Week 3: Train inspection team and implement new procedures. Week 4-6: Execute enhanced inspection with 100% dimensional checks and material property verification for first 3 weeks. Resources needed: 2 additional quality inspectors, precision measuring equipment, and supplier quality agreements. Responsible parties: Quality Manager (overall), Supplier Quality Engineer (supplier interface), Incoming Inspection Lead (execution). Success criteria: <50 PPM defective components accepted, 99% on-time inspection completion, supplier corrective action plan if issues identified.",
        q3_risks: "Risk 1: Increased inspection costs and cycle time could impact production flow - Mitigation: Implement risk-based sampling after initial period and work with supplier to improve quality at source. Risk 2: Supplier relationship strain due to increased scrutiny - Mitigation: Frame as partnership for mutual improvement and provide clear feedback mechanisms. Risk 3: Potential for over-inspection creating bottlenecks - Mitigation: Use statistical process control to optimize inspection frequency and automate where possible. Risk 4: Internal resistance to new procedures - Mitigation: Communicate benefits clearly and provide comprehensive training with management support."
      },
      4: {
        q4_metrics: "Leading indicators: 1) Incoming inspection defect rate (daily) - early signal of supplier quality, 2) First-pass yield at each assembly station (real-time) - immediate feedback on process effectiveness, 3) Process capability indices (weekly) - trending of process stability, 4) Employee training completion rate (weekly) - ensures competency development. Lagging indicators: 1) Customer return rate (monthly) - ultimate measure of external quality, 2) Warranty cost reduction (monthly) - financial impact measurement, 3) Overall equipment effectiveness (weekly) - comprehensive productivity measure, 4) Customer satisfaction scores (quarterly) - long-term relationship health.",
        q4_timeline: "Implementation Phase (Weeks 1-4): Deploy enhanced inspection protocols and complete operator retraining. Initial Improvement Phase (Weeks 5-12): Expect 30-50% reduction in internal defect detection as processes stabilize. Full Impact Assessment (Weeks 13-24): Measure complete impact on customer returns and warranty costs, with expected 60-80% improvement. Review checkpoints at weeks 4, 8, 16, and 24 to assess progress and adjust strategies. Timeframes are based on typical manufacturing improvement cycles and allow for process stabilization and data collection.",
        q4_sustainability: "Training: Develop standard operating procedures with visual aids and implement skills matrices to ensure ongoing competency. Process standardization: Create detailed work instructions with mistake-proofing elements and implement layered process audits. Accountability: Establish daily management review meetings with visual dashboards showing key metrics and assign ownership for each metric. Continuous improvement: Implement monthly kaizen events focused on quality improvement and establish a suggestion system for operator input on process improvements. Create a quality improvement roadmap with quarterly reviews to ensure sustained focus and advancement."
      },
      5: {
        q5_verbal: "Audio recording for good response would demonstrate comprehensive understanding of manufacturing problem-solving methodology with clear communication skills."
      }
    },
    bad: {
      1: {
        q1_data: "I would look at production numbers and see if anything looks wrong. Maybe check some quality reports and ask people what's happening. I think we need to count defects and see which ones are bad.",
        q1_stakeholders: "I would talk to the manager and some workers to see what they think. Maybe the quality person too. The supervisor would probably know what's going on.",
        q1_observations: "I would walk around the factory and see if anything looks different. Check if machines are working properly and see if people are doing their jobs right."
      },
      2: {
        q2_causes: "The machines might be broken or the workers aren't doing their job right. Maybe the new parts are bad quality. Could be that the process isn't working anymore.",
        q2_method: "I would ask why this is happening and keep asking why until I find the answer. Maybe make a fish diagram to see all the reasons.",
        q2_validation: "I would check if my ideas are right by looking at the data and seeing if it makes sense. Maybe test some things to see what happens."
      },
      3: {
        q3_solutions: "Fix the machines and train the workers better. Make sure the supplier sends good parts. Check everything more carefully.",
        q3_implementation: "First fix the machines, then train people, then check the supplier. It should take a few weeks to do everything. The maintenance people can fix the machines and HR can train workers.",
        q3_risks: "It might cost too much money or take too long. People might not like the changes. The supplier might get upset."
      },
      4: {
        q4_metrics: "Count how many defects we have each day and see if customers complain less. Check if the machines are working better.",
        q4_timeline: "It should get better in a few weeks after we fix everything. We can check every month to see if it's working.",
        q4_sustainability: "Make sure people remember the training and keep doing things the right way. Have someone check that everything is still working properly."
      },
      5: {
        q5_verbal: "Audio recording for bad response would demonstrate limited understanding with unclear communication."
      }
    }
  };

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

  const handleDemoGoodAnswers = () => {
    if (!sessionData) return;
    setDemoMode('good');
  };

  const handleDemoBadAnswers = () => {
    if (!sessionData) return;
    setDemoMode('bad');
  };

  const getDemoResponsesForCurrentPart = () => {
    if (!demoMode) return null;
    return demoData[demoMode][currentPart] || null;
  };

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  const handlePartSubmit = async (partId, responses, audioData = null) => {
    setIsSubmitting(true);
    setShowLoadingOverlay(true);
    
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
          // Scroll to top when next part loads
          setTimeout(() => {
            scrollToTop();
          }, 100);
        } else {
          // All parts completed, show final results
          setShowFinalResults(true);
          setTimeout(() => {
            scrollToTop();
          }, 100);
        }
      }

    } catch (error) {
      console.error('Error submitting part:', error);
      alert('Error submitting part. Please try again.');
    } finally {
      setIsSubmitting(false);
      setShowLoadingOverlay(false);
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
      {/* Loading Overlay */}
      {showLoadingOverlay && (
        <div className="loading-overlay">
          <div className="loading-content">
            <div className="loading-spinner"></div>
            <h3>Evaluating Your Response...</h3>
            <p>Please wait while we analyze your answers and prepare the next part.</p>
          </div>
        </div>
      )}
      
      <div className={`main-content ${showLoadingOverlay ? 'blurred' : ''}`}>
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
                demoResponses={getDemoResponsesForCurrentPart()}
                onDemoModeChange={setDemoMode}
              />
            )
          ))}
        </div>
         
        <div className="demo-controls">
            <p className="demo-label"><strong>Demo Mode:</strong> Auto-fill current part with sample responses</p>
            <div className="demo-buttons">
              <button 
                onClick={handleDemoGoodAnswers}
                disabled={isSubmitting || showFinalResults}
                className="demo-button demo-good"
              >
                🎯 Fill: Good Responses
              </button>
              <button 
                onClick={handleDemoBadAnswers}
                disabled={isSubmitting || showFinalResults}
                className="demo-button demo-bad"
              >
                ❌ Fill: Poor Responses
              </button>
            </div>
            <p className="demo-description">
              Demo buttons auto-fill the current part with sample answers. You can then review and submit manually.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MultiPartEvaluation; 