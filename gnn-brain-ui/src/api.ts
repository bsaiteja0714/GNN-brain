export const providerNames = { openai: 'OpenAI', groq: 'Groq', gemini: 'Google AI Studio (Gemini)' }
export type Provider = { provider: keyof typeof providerNames; model: string; key: string }
export const defaultModels: Record<Provider['provider'], string> = {
  openai: 'gpt-5-mini', groq: 'openai/gpt-oss-20b', gemini: 'gemini-3.5-flash-lite',
}

export async function post<T>(path: string, payload: unknown, signal: AbortSignal, key?: string): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (key) headers['X-Provider-Key'] = key
  const response = await fetch('/api' + path, { method: 'POST', headers, body: JSON.stringify(payload), signal })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(typeof body?.detail === 'string' ? body.detail : 'The request failed. Check that the backend is running.')
  }
  return response.json() as Promise<T>
}


