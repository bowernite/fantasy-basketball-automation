const FETCH_TIMEOUT_MS = 20 * 1000;

/** `fetch` that rejects if the response (body included) takes over 20 s */
export function fetchWithTimeout(input: string | URL, init: RequestInit = {}) {
  const controller = new AbortController();
  const { hostname } = new URL(input);
  setTimeout(() => controller.abort(new Error(`Request to ${hostname} timed out after ${FETCH_TIMEOUT_MS / 1000} s`)), FETCH_TIMEOUT_MS);
  return fetch(input, { ...init, signal: controller.signal });
}
