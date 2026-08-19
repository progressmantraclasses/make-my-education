/**
 * HomePage.jsx
 * Responsibility: Compose the home page — manages query state, API call, multi-session history.
 */
import { useState, useEffect, useRef } from "react";

import AnswerCard from "../components/AnswerCard";
import LoadingSpinner from "../components/LoadingSpinner";
import QueryInput from "../components/QueryInput";
import { postQuery } from "../api/queryApi";

const EXAMPLE_QUESTIONS = [
  "Which colleges offer scholarships for low-income families?",
  "I scored 78% with \u20b91.5 lakh/year budget \u2014 which engineering colleges?",
  "Which colleges offer an MBA, and what do they cost?",
  "List the government colleges that have hostel facilities.",
];

function loadSessions() {
  try {
    const saved = localStorage.getItem("mme_sessions");
    if (saved) return JSON.parse(saved);
  } catch (e) {
    console.error("Failed to parse sessions from localStorage", e);
  }
  return [];
}

function saveSessions(sessions) {
  localStorage.setItem("mme_sessions", JSON.stringify(sessions));
}

function loadActiveSession() {
  try {
    const saved = localStorage.getItem("mme_active_session");
    if (saved) return JSON.parse(saved);
  } catch (e) {
    console.error("Failed to parse active session from localStorage", e);
  }
  return [];
}

export default function HomePage() {
  const [isLoading, setIsLoading]         = useState(false);
  const [errorMessage, setErrorMessage]   = useState(null);
  // Current active chat messages (now persisted)
  const [messages, setMessages]           = useState(() => loadActiveSession());
  // All saved past sessions (each has id, title, messages, createdAt)
  const [sessions, setSessions]           = useState(() => loadSessions());
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const messagesEndRef = useRef(null);

  // Persist sessions and active chat to localStorage on every change
  useEffect(() => {
    saveSessions(sessions);
  }, [sessions]);

  useEffect(() => {
    localStorage.setItem("mme_active_session", JSON.stringify(messages));
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Save current chat as a past session and open a fresh blank chat
  function handleNewChat() {
    if (messages.length === 0) return; // Already blank, nothing to save
    const session = {
      id:        Date.now(),
      title:     messages[0]?.queryText || "Chat",
      messages:  messages,
      createdAt: new Date().toISOString(),
    };
    setSessions((prev) => [session, ...prev]);
    setMessages([]);
    setErrorMessage(null);
  }

  // Restore a saved session into the active view
  function handleRestoreSession(session) {
    if (messages.length > 0) {
      // Save the currently active chat first
      const current = {
        id:        Date.now(),
        title:     messages[0]?.queryText || "Chat",
        messages:  messages,
        createdAt: new Date().toISOString(),
      };
      setSessions((prev) => [current, ...prev.filter((s) => s.id !== session.id)]);
    } else {
      setSessions((prev) => prev.filter((s) => s.id !== session.id));
    }
    setMessages(session.messages);
    setErrorMessage(null);
  }

  async function handleQuerySubmit(queryText) {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const apiResponse = await postQuery(queryText);
      const historyEntry = {
        id:                 Date.now(),
        queryText,
        answer:             apiResponse.answer,
        citations:          apiResponse.citations,
        answered:           apiResponse.answered,
        reasonIfUnanswered: apiResponse.reason_if_unanswered,
        followUpQuestions:  apiResponse.follow_up_questions || [],
      };
      setMessages((prev) => [...prev, historyEntry]);
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
      {/* Sidebar */}
      <aside className={`sidebar ${isSidebarOpen ? "sidebar--open" : "sidebar--closed"}`}>
        <div className="sidebar__logo">
          <span className="sidebar__logo-make">MAKE</span>
          <span className="sidebar__logo-my">My</span>
          <span className="sidebar__logo-edu">EDU</span>
        </div>
        <div className="sidebar__header">
          <button
            className="new-chat-btn"
            onClick={handleNewChat}
            title="New Chat"
          >
            + New Chat
          </button>
          <button
            className="sidebar-toggle-btn"
            onClick={() => setIsSidebarOpen(false)}
            title="Close sidebar"
          >
            &times;
          </button>
        </div>
        <div className="sidebar__history">
          <p className="sidebar__history-label">Recent Chats</p>
          {sessions.length === 0 && messages.length === 0 && (
            <p className="sidebar__history-empty">No history yet. Ask a question!</p>
          )}
          {/* Currently active unsaved session preview */}
          {messages.length > 0 && (
            <div className="history-item history-item--active" title={messages[0]?.queryText}>
              <span className="history-item__icon">💬</span>
              <span className="history-item__text">{messages[0]?.queryText}</span>
            </div>
          )}
          {/* Past saved sessions */}
          {sessions.map((session) => (
            <div
              key={session.id}
              className="history-item"
              title={session.title}
              onClick={() => handleRestoreSession(session)}
              style={{ cursor: "pointer" }}
            >
              <span className="history-item__icon">💬</span>
              <span className="history-item__text">{session.title}</span>
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
                &#9776;
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
          {messages.length === 0 ? (
            <div className="hero-wrapper">
              <header className="hero">
                <div className="hero__badge">AI-Powered &middot; RAG &middot; Grounded Answers</div>
                <h1 className="hero__title">
                  MAKE <span className="hero__title--my">My</span>{" "}
                  <span className="hero__title--accent">EDUCATION</span>
                </h1>
                <p className="hero__subtitle">
                  Ask any question about colleges &mdash; fees, placements, scholarships,
                  hostel, cutoffs and more. Every answer is grounded in verified data.
                </p>
              </header>
            </div>
          ) : (
            <div className="answers-list">
              {messages.map((entry) => (
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
              <span className="error-banner__icon">&#9888;</span>
              <span>{errorMessage}</span>
            </div>
          )}
        </div>

        {/* Fixed bottom input */}
        <div className="chat-input-container">
          <div className="chat-input-wrapper">
            {messages.length === 0 && (
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
            Make My Education &middot; RAG College Advisor &middot; All answers grounded in verified dataset
          </div>
        </div>
      </main>
    </div>
  );
}
