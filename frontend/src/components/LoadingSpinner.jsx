/**
 * LoadingSpinner.jsx
 * Responsibility: Render an animated loading indicator only.
 */
import { useState, useEffect } from "react";

const REASONING_STEPS = [
  "Searching knowledge base",
  "Analyzing college details",
  "Comparing parameters",
  "Thinking",
  "Synthesizing answer",
  "Finding relevant facts",
  "Finalizing"
];

export default function LoadingSpinner() {
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStepIndex((prev) => (prev + 1) % REASONING_STEPS.length);
    }, 600); // Change text every 600ms
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="chat-message">
      <div className="chat-message__bot">
        <span className="chat-message__avatar chat-message__avatar--bot">🎓</span>
        <div className="chat-message__response">
          <div className="reasoning-pill">
            <div className="reasoning-spinner"></div>
            <span className="reasoning-text">{REASONING_STEPS[stepIndex]}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
