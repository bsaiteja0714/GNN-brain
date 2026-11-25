import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import Icon from './Icon'

import { defaultModels, post, providerNames } from './api'
import type { Provider } from './api'

type Props = {
  current: Provider | null
  onClose: () => void
  onConnect: (provider: Provider) => void
  onDisconnect: () => void
}

export default function ProviderDialog({ current, onClose, onConnect, onDisconnect }: Props) {
  const dialog = useRef<HTMLDialogElement>(null)
  const request = useRef<AbortController | null>(null)
  const [provider, setProvider] = useState<Provider['provider']>(current?.provider ?? 'openai')
  const [model, setModel] = useState(current?.model ?? defaultModels.openai)
  const [key, setKey] = useState('')
  const [error, setError] = useState('')
  const [checking, setChecking] = useState(false)

  useEffect(() => {
    const element = dialog.current
    element?.showModal()
    return () => { request.current?.abort(); element?.close() }
  }, [])

  async function connect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (request.current || !key.trim() || !model.trim()) return
    const controller = new AbortController()
    request.current = controller
    setChecking(true)
    setError('')
    try {
      await post('/assistant/connection', { provider, model: model.trim() },
        AbortSignal.any([controller.signal, AbortSignal.timeout(45_000)]), key.trim())
      if (!controller.signal.aborted) onConnect({ provider, model: model.trim(), key: key.trim() })
    } catch (failure) {
      if (!controller.signal.aborted) {
        setError(failure instanceof Error ? failure.message : 'Could not connect to the provider.')
        setChecking(false)
      }
    } finally {
      request.current = null
    }
  }

  return (
    <dialog className="provider-dialog" ref={dialog} aria-labelledby="provider-title"
      onCancel={event => { event.preventDefault(); onClose() }}>
      <div className="dialog-heading">
        <span className="dialog-icon"><Icon name="plug" /></span>
        <button className="icon-button" aria-label="Close provider settings" onClick={onClose}><Icon name="close" /></button>
      </div>
      <h2 id="provider-title">AI provider</h2>
      <p>Connect a model to explain the current graph or draft changes.</p>
      <form onSubmit={connect}>
        <label>Provider<select value={provider} onChange={event => {
          const next = event.target.value as Provider['provider']
          setProvider(next)
          setModel(defaultModels[next])
          setKey('')
          setError('')
        }} disabled={checking}>
          {Object.entries(providerNames).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select></label>
        <label>Model<input value={model} onChange={event => setModel(event.target.value)} maxLength={120} required disabled={checking} /></label>
        <label>API key<input type="password" value={key} onChange={event => setKey(event.target.value)}
          autoComplete="off" placeholder={current ? 'Enter a key to replace the connection' : 'Enter your provider API key'}
          maxLength={512} required disabled={checking} /></label>
        {provider === 'gemini' && <a className="provider-key-link" href="https://aistudio.google.com/api-keys"
          target="_blank" rel="noreferrer">Get a Gemini API key from Google AI Studio</a>}
        <p className="provider-note">Assistant requests send the full active graph, your question and recent chat to {providerNames[provider]}. The key is kept in this tab’s memory.</p>
        {error && <p className="request-error" role="alert">{error}</p>}
        <footer>
          {current && <button type="button" className="quiet-button disconnect" onClick={onDisconnect} disabled={checking}>Disconnect</button>}
          <button className="primary-button" type="submit" disabled={checking || !key.trim() || !model.trim()}>
            {checking ? 'Checking connection…' : 'Verify and connect'}
          </button>
        </footer>
      </form>
    </dialog>
  )
}

