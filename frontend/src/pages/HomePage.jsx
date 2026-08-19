/**
 * HomePage.jsx
 * Responsibility: Compose the home page — manages query state, API call, history.
 */
import { useState, useEffect, useRef } from "react";

import AnswerCard from "../components/AnswerCard";
import LoadingSpinner from "../components/LoadingSpinner";
import QueryInput from "../components/QueryInput";
import { postQuery } from "../api/queryApi";

// Example questions shown as quick-select chips
const EXAMPLE_QUESTIONS = [
  "Which colleges offer scholarships for low-income families?",
  "I scored 78% with ₹1.5 lakh/year budget — which engineering colleges?",
  "Which colleges offer an MBA, and what do they cost?",
  "List the government colleges that have hostel facilities.",
];

export default function HomePage() {
  const [isLoading, setIsLoading]           = useState(false);
  const [errorMessage, setErrorMessage]     = useState(null);
  const [answerHistory, setAnswerHistory]   = useState(() => {
    try {
      const saved = localStorage.getItem("makeMyEducationHistory");
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.error("Failed to parse history from local storage", e);
    }
    return [];
  }); // newest first
  const [isSidebarOpen, setIsSidebarOpen]   = useState(false);

  // Save to local storage whenever answerHistory changes
  useEffect(() => {
    localStorage.setItem("makeMyEducationHistory", JSON.stringify(answerHistory));
  }, [answerHistory]);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [answerHistory, isLoading]);

  async function handleQuerySubmit(queryText) {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const apiResponse = await postQuery(queryText);

      const historyEntry = {
        id:                  Date.now(),
        queryText,
        answer:              apiResponse.answer,
        citations:           apiResponse.citations,
        answered:            apiResponse.answered,
        reasonIfUnanswered:  apiResponse.reason_if_unanswered,
        followUpQuestions:   apiResponse.follow_up_questions || [],
      };

      // Prepend newest answer to top of history
      setAnswerHistory((prevHistory) => [historyEntry, ...prevHistory]);
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleExampleClick(exampleQuestion) {
    if (!isLoading) {
      handleQuerySubmit(exampleQuestion);
    }
  }

  return (
    <div className="chat-layout">
      {/* Sidebar for History */}
      <aside className={`sidebar ${isSidebarOpen ? "sidebar--open" : "sidebar--closed"}`}>
        <div className="sidebar__logo">
          <span className="sidebar__logo-make">MAKE</span>
          <span className="sidebar__logo-my">My</span>
          <span className="sidebar__logo-edu">EDU</span>
        </div>
        <div className="sidebar__header">
          <button
            className="new-chat-btn"
            onClick={() => setAnswerHistory([])}
            title="New Chat"
          >
            + New Chat
          </button>
          <button 
            className="sidebar-toggle-btn" 
            onClick={() => setIsSidebarOpen(false)}
            title="Close sidebar"
          >
            ✕
          </button>
        </div>
        <div className="sidebar__history">
          <p className="sidebar__history-label">Recent Chats</p>
          {answerHistory.length === 0 && (
            <p className="sidebar__history-empty">No history yet. Ask a question!</p>
          )}
          {answerHistory.map((entry) => (
            <div key={entry.id} className="history-item" title={entry.queryText}>
              <span className="history-item__icon">💬</span>
              <span className="history-item__text">{entry.queryText}</span>
            </div>
          ))}
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="chat-main">
        {(!isSidebarOpen) && (
          <header className="chat-header">
            <div className="chat-header__controls">
              <button 
                className="sidebar-toggle-btn sidebar-toggle-btn--floating" 
                onClick={() => setIsSidebarOpen(true)}
                title="Open sidebar"
              >
                ☰
              </button>
              <div className="chat-header__logo">
                <span className="sidebar__logo-make">MAKE</span>
                <span className="sidebar__logo-my">My</span>
                <span className="sidebar__logo-edu">EDU</span>
              </div>
            </div>
          </header>
        )}
        <div className="chat-content">
          {answerHistory.length === 0 ? (
            <div className="hero-wrapper">
              <header className="hero">
                <div className="hero__badge">AI-Powered · RAG · Grounded Answers</div>
                <h1 className="hero__title">
                  MAKE <span className="hero__title--my">My</span> <span className="hero__title--accent">EDUCATION</span>
                </h1>
                <p className="hero__subtitle">
                  Ask any question about colleges — fees, placements, scholarships, hostel,
                  cutoffs and more. Every answer is grounded in verified data.
                </p>
              </header>
            </div>
          ) : (
            <div className="answers-list">
              {answerHistory.slice().reverse().map((entry) => (
                <div key={entry.id} className="chat-message">
                  <div className="chat-message__user">
                    <span className="chat-message__avatar">U</span>
                    <p className="chat-message__text">{entry.queryText}</p>
                  </div>
                  <div className="chat-message__bot">
                    <span className="chat-message__avatar chat-message__avatar--bot">🎓</span>
                    <div className="chat-message__response">
                      <AnswerCard
                        queryText={entry.queryText}
                        answer={entry.answer}
                        citations={entry.citations}
                        answered={entry.answered}
                        reasonIfUnanswered={entry.reasonIfUnanswered}
                        followUpQuestions={entry.followUpQuestions}
                        onFollowUpClick={handleExampleClick}
                      />
                    </div>
                  </div>
                </div>
              ))}
              {isLoading && <LoadingSpinner />}
              <div ref={messagesEndRef} />
            </div>
          )}
          {errorMessage && (
            <div className="error-banner" role="alert">
              <span className="error-banner__icon">⚠</span>
              <span>{errorMessage}</span>
            </div>
          )}
        </div>

        {/* Fixed bottom input */}
        <div className="chat-input-container">
          <div className="chat-input-wrapper">
            {answerHistory.length === 0 && (
              <div className="examples-container">
                <div className="examples-row">
                  <button className="example-chip" onClick={() => handleExampleClick(EXAMPLE_QUESTIONS[0])} disabled={isLoading}>
                    {EXAMPLE_QUESTIONS[0]}
                  </button>
                </div>
                <div className="examples-row">
                  <button className="example-chip" onClick={() => handleExampleClick(EXAMPLE_QUESTIONS[1])} disabled={isLoading}>
                    {EXAMPLE_QUESTIONS[1]}
                  </button>
                </div>
                <div className="examples-row">
                  <button className="example-chip" onClick={() => handleExampleClick(EXAMPLE_QUESTIONS[2])} disabled={isLoading}>
                    {EXAMPLE_QUESTIONS[2]}
                  </button>
                  <button className="example-chip" onClick={() => handleExampleClick(EXAMPLE_QUESTIONS[3])} disabled={isLoading}>
                    {EXAMPLE_QUESTIONS[3]}
                  </button>
                </div>
              </div>
            )}
            <QueryInput onSubmit={handleQuerySubmit} isLoading={isLoading} />
          </div>
          <div className="chat-footer">
            Make My Education · RAG College Advisor · All answers grounded in verified dataset
          </div>
        </div>
      </main>
    </div>
  );
}
