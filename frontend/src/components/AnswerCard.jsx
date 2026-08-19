/**
 * AnswerCard.jsx
 * Responsibility: Display the RAG answer, citations, and unanswered reason only.
 *
 * Props:
 *   queryText (string)      : the original question asked
 *   answer (string)         : the answer text from the API
 *   citations (string[])    : array of college_id strings e.g. ["C001","C004"]
 *   answered (bool)         : whether the question was answerable
 *   reasonIfUnanswered (str): explanation when answered=false
 */
import React from 'react';

function renderInlineFormatting(text) {
  // Split by **bold**, *italic*, or `code`
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);

  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={index}>{part.slice(1, -1)}</em>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={index} className="inline-code">{part.slice(1, -1)}</code>;
    }
    return part;
  });
}

function formatText(text) {
  if (!text) return null;

  // Split text into paragraphs based on double newlines
  const paragraphs = text.split(/\n\n+/);

  return paragraphs.map((paragraph, pIndex) => {
    // If it looks like a list (lines starting with - or *)
    if (/^[\-\*]\s/m.test(paragraph)) {
      const listItems = paragraph.split('\n').filter(line => line.trim());
      return (
        <ul key={`p-${pIndex}`} className="answer-list">
          {listItems.map((item, iIndex) => {
            const cleanItem = item.replace(/^[\-\*]\s+/, '');
            return <li key={`li-${iIndex}`}>{renderInlineFormatting(cleanItem)}</li>;
          })}
        </ul>
      );
    }
    // If the paragraph doesn't look like a list, render it with <br/> for single newlines
    return (
      <p key={`p-${pIndex}`} className="answer-paragraph">
        {paragraph.split('\n').map((line, lineIdx, arr) => (
          <React.Fragment key={`br-${pIndex}-${lineIdx}`}>
            {renderInlineFormatting(line)}
            {lineIdx < arr.length - 1 && <br />}
          </React.Fragment>
        ))}
      </p>
    );
  });
}
export default function AnswerCard({
  queryText,
  answer,
  citations,
  answered,
  reasonIfUnanswered,
  followUpQuestions,
  onFollowUpClick,
}) {
  return (
    <div className={`answer-card ${!answered ? "answer-card--unanswered" : ""}`}>
      {/* Question echo */}
      <div className="answer-card__question">
        <span className="answer-card__q-label">You asked</span>
        <p className="answer-card__q-text">{queryText}</p>
      </div>

      {/* Status badge */}
      <div className={`answer-badge ${answered ? "answer-badge--ok" : "answer-badge--na"}`}>
        {answered ? "✓ Answered" : "⚠ Cannot Answer"}
      </div>

      {/* Answer body */}
      <div className="answer-card__body">
        <div className="answer-card__text">
          {formatText(answer)}
        </div>

        {!answered && reasonIfUnanswered && (
          <p className="answer-card__reason">
            <strong>Reason: </strong>{reasonIfUnanswered}
          </p>
        )}
      </div>

      {/* Citations */}
      {answered && citations && citations.length > 0 && (
        <div className="answer-card__citations">
          <span className="citations-label">Sources</span>
          <div className="citations-chips">
            {citations.map((collegeId) => (
              <span key={collegeId} className="citation-chip">
                {collegeId}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Follow-ups */}
      {followUpQuestions && followUpQuestions.length > 0 && (
        <div className="answer-card__followups">
          <span className="followups-label">Follow-ups</span>
          <div className="followups-list">
            {followUpQuestions.map((q, idx) => (
              <button 
                key={idx} 
                className="followup-item" 
                onClick={() => onFollowUpClick && onFollowUpClick(q)}
              >
                <span className="followup-item__icon">↳</span>
                <span className="followup-item__text">{q}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
