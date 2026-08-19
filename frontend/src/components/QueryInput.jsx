/**
 * QueryInput.jsx
 * Responsibility: Render the search bar and handle form submission only.
 *
 * Props:
 *   onSubmit (fn)     : called with (queryText: string) when user submits
 *   isLoading (bool)  : disables input and button while request is in flight
 */
import { useState } from "react";

export default function QueryInput({ onSubmit, isLoading }) {
  const [inputValue, setInputValue] = useState("");

  function handleFormSubmit(event) {
    event.preventDefault();
    const trimmedQuery = inputValue.trim();
    if (!trimmedQuery || isLoading) return;
    onSubmit(trimmedQuery);
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      handleFormSubmit(event);
    }
  }

  return (
    <form className="query-form" onSubmit={handleFormSubmit} noValidate>
      <div className="input-wrapper">
        <span className="input-icon" aria-hidden="true">🎓</span>
        <textarea
          id="query-input"
          className="query-textarea"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask me anything about colleges... e.g. Which colleges offer an MBA?"
          disabled={isLoading}
          rows={2}
          maxLength={2000}
          aria-label="College question input"
        />
        <button
          id="query-submit-btn"
          type="submit"
          className={`submit-btn ${isLoading ? "submit-btn--loading" : ""}`}
          disabled={isLoading || !inputValue.trim()}
          aria-label="Submit question"
        >
          {isLoading ? "..." : "Ask →"}
        </button>
      </div>
      <p className="query-hint">Press Enter to submit · Shift+Enter for new line</p>
    </form>
  );
}
