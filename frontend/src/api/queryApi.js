/**
 * queryApi.js
 * Responsibility: HTTP communication with the FastAPI backend only.
 *   - postQuery : POST /api/query → returns response JSON
 */

const API_BASE_URL = "/api";

/**
 * Send a natural-language query to the RAG backend.
 *
 * @param {string} queryText - The user's question
 * @returns {Promise<{answer: string, citations: string[], answered: boolean, reason_if_unanswered: string|null}>}
 * @throws {Error} on network failure or non-2xx HTTP status
 */
export async function postQuery(queryText) {
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: queryText }),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const errorMessage = errorBody.detail || `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(errorMessage);
  }

  return response.json();
}
