/**
 * DecisionTrace Component
 * 
 * Displays decision traces explaining why personas were assigned and content selected
 */

import React, { useState } from 'react';

const DecisionTrace = ({ traces }) => {
  const [expandedPersona30d, setExpandedPersona30d] = useState(false);
  const [expandedPersona180d, setExpandedPersona180d] = useState(false);
  const [expandedContent, setExpandedContent] = useState(false);

  if (!traces || traces.length === 0) {
    return (
      <div className="decision-trace">
        <h3>Decision Traces</h3>
        <p className="no-data">No traces available</p>
      </div>
    );
  }

  // Organize traces by type
  const personaTraces = traces.filter(t => t.trace_type === 'persona_assignment' || 
                                            t.trace_content?.trace_type === 'persona_assignment');
  const contentTraces = traces.filter(t => t.trace_type === 'content_selection' || 
                                            t.trace_content?.trace_type === 'content_selection');

  const persona30d = personaTraces.find(t => {
    const content = t.trace_content || t;
    return content.window_days === 30;
  });

  const persona180d = personaTraces.find(t => {
    const content = t.trace_content || t;
    return content.window_days === 180;
  });

  const latestContent = contentTraces[0];

  const renderPersonaTrace = (trace, window) => {
    if (!trace) return <p className="no-data">Not available</p>;

    const content = trace.trace_content || trace;

    return (
      <div className="trace-details">
        <p><strong>Persona:</strong> {content.primary_persona_name || 'Stable'}</p>
        <p><strong>Status:</strong> {content.status}</p>
        <p className="rationale">{content.rationale}</p>
        
        {content.criteria_met && Object.keys(content.criteria_met).length > 0 && (
          <details className="trace-criteria">
            <summary>Criteria Met</summary>
            <pre>{JSON.stringify(content.criteria_met, null, 2)}</pre>
          </details>
        )}

        {content.feature_values_cited && Object.keys(content.feature_values_cited).length > 0 && (
          <details className="trace-features">
            <summary>Feature Values</summary>
            <pre>{JSON.stringify(content.feature_values_cited, null, 2)}</pre>
          </details>
        )}
      </div>
    );
  };

  const renderContentTrace = (trace) => {
    if (!trace) return <p className="no-data">Not available</p>;

    const content = trace.trace_content || trace;

    return (
      <div className="trace-details">
        {content.educational_items && content.educational_items.length > 0 && (
          <div className="trace-section">
            <h5>Educational Content Selection</h5>
            {content.educational_items.map((item, idx) => (
              <div key={idx} className="trace-item">
                <p><strong>{item.title}</strong></p>
                <p className="reason">{item.selected_reason}</p>
              </div>
            ))}
          </div>
        )}

        {content.partner_offers && content.partner_offers.length > 0 && (
          <div className="trace-section">
            <h5>Partner Offer Selection</h5>
            {content.partner_offers.map((item, idx) => (
              <div key={idx} className="trace-item">
                <p><strong>{item.title}</strong></p>
                <p className="reason">{item.selected_reason}</p>
                <p className={`eligibility ${item.eligibility_passed ? 'passed' : 'failed'}`}>
                  Eligibility: {item.eligibility_passed ? 'Passed' : 'Failed'}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="decision-trace">
      <h3>Decision Traces</h3>

      {/* 30d Persona Trace */}
      <div className="trace-section">
        <div 
          className="trace-header"
          onClick={() => setExpandedPersona30d(!expandedPersona30d)}
        >
          <h4>Why this persona? (30d window)</h4>
          <span className="expand-icon">{expandedPersona30d ? '▼' : '▶'}</span>
        </div>
        {expandedPersona30d && renderPersonaTrace(persona30d, 30)}
      </div>

      {/* 180d Persona Trace */}
      <div className="trace-section">
        <div 
          className="trace-header"
          onClick={() => setExpandedPersona180d(!expandedPersona180d)}
        >
          <h4>Why this persona? (180d window)</h4>
          <span className="expand-icon">{expandedPersona180d ? '▼' : '▶'}</span>
        </div>
        {expandedPersona180d && renderPersonaTrace(persona180d, 180)}
      </div>

      {/* Content Selection Trace */}
      <div className="trace-section">
        <div 
          className="trace-header"
          onClick={() => setExpandedContent(!expandedContent)}
        >
          <h4>Why this content?</h4>
          <span className="expand-icon">{expandedContent ? '▼' : '▶'}</span>
        </div>
        {expandedContent && renderContentTrace(latestContent)}
      </div>
    </div>
  );
};

export default DecisionTrace;

