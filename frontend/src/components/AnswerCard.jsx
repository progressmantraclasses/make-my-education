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
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
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
            <div className="answer-text markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {answer}
              </ReactMarkdown>
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
                <span className="followup-item__text">
                  <ReactMarkdown components={{ p: 'span' }} remarkPlugins={[remarkGfm]}>
                    {q}
                  </ReactMarkdown>
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
