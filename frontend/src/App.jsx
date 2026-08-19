/**
 * App.jsx
 * Responsibility: Root app shell — renders the page layout and routes.
 */
import HomePage from "./pages/HomePage";

export default function App() {
  return (
    <div className="app-shell">
      <HomePage />
    </div>
  );
}
