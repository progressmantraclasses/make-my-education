/**
 * AnswerCard.jsx
 * Responsibility: Display the RAG answer, citations, and follow-up questions.
 *
 * Props:
 *   queryText (string)          : the original question asked
 *   answer (string)             : the answer text from the API
 *   citations (string[])        : array of college_id strings e.g. ["C001","C004"]
 *   answered (bool)             : whether the question was answerable
 *   reasonIfUnanswered (str)    : explanation when answered=false
 *   followUpQuestions (string[]): follow-up questions from the API follow_up_questions array
 *   onFollowUpClick (fn)        : callback when a follow-up is clicked
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
  const rawAnswer = answer || "";
  let cleanedAnswer = rawAnswer;
  let parsedFollowUps = followUpQuestions || [];

  // Frontend parsing: Extract follow-up section from answer string and turn them into clickable buttons
  const followUpPattern = /(?:\n+[-*_]{3,})?\n+[\s#*_>]*(follow[- ]?up|possible[- ](?:next[- ])?questions?|related[- ]questions?|you[- ]might[- ](?:also[- ])?ask|next[- ](?:steps?|questions?)|further[- ]reading|questions?[- ](?:you[- ]might[- ]consider|to[- ]explore|for[- ]you))([\s\S]*)/i;
  
  const match = rawAnswer.match(followUpPattern);
  if (match && match[2]) {
    // We found a follow-up section. Remove it from the main answer text.
    cleanedAnswer = rawAnswer.substring(0, match.index).trim();
    
    // Extract individual questions (lines starting with a number or bullet)
    const questionsText = match[2];
    const questionLines = questionsText.split('\n');
    const extractedQuestions = [];
    
    for (let line of questionLines) {
      line = line.trim();
      // Match lines starting with "1. ", "- ", "* ", or just any non-empty line that looks like a question
      const lineMatch = line.match(/^(\d+\.|[-*])\s+(.+)/);
      if (lineMatch && lineMatch[2]) {
        extractedQuestions.push(lineMatch[2].trim());
      } else if (line.length > 10 && line.endsWith("?")) {
        // Fallback: if it's a question but missing bullet point
        extractedQuestions.push(line);
      }
    }
    
    if (extractedQuestions.length > 0) {
      parsedFollowUps = extractedQuestions;
    }
  }

  const hasFollowUps = Array.isArray(parsedFollowUps) && parsedFollowUps.length > 0;
  const hasCitations = Array.isArray(citations) && citations.length > 0;

  return (
    <div className={`answer-card ${!answered ? "answer-card--unanswered" : ""}`}>
      {/* Question echo */}
      <div className="answer-card__question">
        <span className="answer-card__q-label">You asked</span>
        <p className="answer-card__q-text">{queryText}</p>
      </div>

      {/* Status badge */}
      <div className={`answer-badge ${answered ? "answer-badge--ok" : "answer-badge--na"}`}>
        {answered ? "\u2713 Answered" : "\u26a0 Cannot Answer"}
      </div>

      {/* Answer body */}
      <div className="answer-card__body">
        <div className="answer-text markdown-body">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {cleanedAnswer}
          </ReactMarkdown>
        </div>

        {/* Reason shown only when answered=false */}
        {!answered && reasonIfUnanswered && (
          <p className="answer-card__reason">
            <strong>Reason: </strong>{reasonIfUnanswered}
          </p>
        )}
      </div>

      {/* Citations shown when present regardless of answered state */}
      {hasCitations && (
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

      {/* follow_up_questions: block — always rendered from API array, never from answer text */}
      {hasFollowUps && (
        <div className="answer-card__followups">
          <span className="followups-label">follow_up_questions:</span>
          <div className="followups-list">
            {parsedFollowUps.map((q, idx) => (
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
