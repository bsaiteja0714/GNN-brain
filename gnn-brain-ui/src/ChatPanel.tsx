import { useEffect, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import ChatModeSwitch from './ChatModeSwitch'
import Icon from './Icon'
import type { GraphNode, Proposal, SchoolScenario, Theme, Trace } from './school'
import { nodeColor, roleLabel } from './school'
import type { Provider } from './api'
import { providerNames } from './api'
import './ChatPanel.css'

export type Turn = {
  id: number
  question: string
  answer: string
  context?: string | null
  source?: string
  trace?: Trace
  proposal?: Proposal | null
  applied?: boolean
}

export type Thread = { turns: Turn[]; pending?: string; error?: { message: string; question: string } }
export type Mode = 'local' | 'assistant'
type Prompt = { label: string; question: string }

type Props = {
  hidden: boolean
  threadKey: string
  mode: Mode
  theme: Theme
  title: string
  selected: GraphNode | undefined
  provider: Provider | null
  prompts: Prompt[]
  library: SchoolScenario[]
  thread: Thread
  onMode: (mode: Mode) => void
  onClose: () => void
  onProvider: () => void
  onSend: (question: string) => void
  onReplay: (trace: Trace) => void
  onApply: (turn: Turn) => boolean
}

function answerText(text: string): ReactNode {
  return text.split(/(\*\*[^*\n]+\*\*|`[^`\n]+`)/).map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={index}>{part.slice(2, -2)}</strong>
    if (part.startsWith('`') && part.endsWith('`')) return <code key={index}>{part.slice(1, -1)}</code>
    return part
  })
}

function ProposalCard({ proposal, applied, onApply }: { proposal: Proposal; applied?: boolean; onApply: () => boolean }) {
  const [show, setShow] = useState(false)
  const [stale, setStale] = useState(false)
  const labels = [
    ...proposal.added.map(label => 'Add ' + label),
    ...proposal.edited.map(label => 'Edit ' + label),
    ...proposal.removed.map(label => 'Remove ' + label),
  ]
  return (
    <div className="proposal-card">
      <strong>{proposal.mode === 'new' ? 'New graph' : 'Proposed edits'}</strong>
      <p>{proposal.graph.title} · {proposal.graph.nodes.length} nodes · {proposal.graph.links.length} links</p>
      <p>{proposal.added.length} added, {proposal.edited.length} edited, {proposal.removed.length} removed · {proposal.linksAdded} links added, {proposal.linksRemoved} removed</p>
      {labels.length > 0 && <button className="text-button" type="button" aria-expanded={show} onClick={() => setShow(value => !value)}>
        {show ? 'Hide node changes' : 'Show node changes'}
      </button>}
      {show && <ul>{labels.map((label, index) => <li key={index}>{label}</li>)}</ul>}
      <button className="primary-button apply-button" type="button" disabled={applied || stale}
        onClick={() => { if (!onApply()) setStale(true) }}>{applied ? 'Applied' : proposal.mode === 'new' ? 'Create graph' : 'Apply edits'}</button>
      {stale && <p role="alert">The graph changed after this proposal. Ask for a fresh one.</p>}
    </div>
  )
}

function QuestionLibrary({ questions, onSend, pending }: {
  questions: SchoolScenario[]; onSend: (question: string) => void; pending: boolean
}) {
  const [search, setSearch] = useState('')
  const panel = useRef<HTMLDetailsElement>(null)
  const term = search.trim().toLowerCase()
  const filtered = questions.filter(item => [item.label, item.question, item.role, roleLabel[item.role], item.subject]
    .some(field => field?.toLowerCase().includes(term)))

  return (
    <details className="question-library" ref={panel} onKeyDown={event => {
      if (event.key === 'Escape' && panel.current?.open) {
        panel.current.open = false
        panel.current.querySelector('summary')?.focus()
      }
    }}>
      <summary><Icon name="search" /> Question library <span>{questions.length}</span></summary>
      <div className="question-library-content">
        <input type="search" aria-label="Search school questions" placeholder="Search school questions…"
          value={search} onChange={event => setSearch(event.target.value)} />
        <div className="question-library-results" aria-label="School questions">
          {filtered.map(item => <button key={item.question} type="button" disabled={pending} onClick={() => {
            if (panel.current) panel.current.open = false
            setSearch('')
            onSend(item.question)
          }}>
            <span>{item.question}<small>{roleLabel[item.role] ?? item.role}</small></span><Icon name="arrow" />
          </button>)}
          {filtered.length === 0 && <p>No matching school questions.</p>}
        </div>
      </div>
    </details>
  )
}

export default function ChatPanel({ hidden, threadKey, mode, theme, title, selected, provider, prompts, library, thread, onMode, onClose, onProvider, onSend, onReplay, onApply }: Props) {
  const [drafts, setDrafts] = useState<Record<string, string>>({})
  const draft = drafts[threadKey] ?? ''
  function updateDraft(value: string) {
    setDrafts(current => ({ ...current, [threadKey]: value }))
  }
  const body = useRef<HTMLDivElement>(null)
  const last = thread.turns.at(-1)?.id
  const unavailable = mode === 'assistant' && !provider

  useEffect(() => {
    if (body.current) body.current.scrollTop = body.current.scrollHeight
  }, [last, thread.pending, thread.error, hidden, threadKey])

  function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const question = draft.trim()
    if (!question || thread.pending || unavailable) return
    onSend(question)
    updateDraft('')
  }

  return (
    <aside className="chat-panel" aria-label="Chat panel">
      <header className="chat-header">
        <div className="chat-heading"><Icon name="panel" /><h2>Chat</h2></div>
        <button type="button" className="icon-button" aria-label="Close chat" title="Close chat" onClick={onClose}><Icon name="close" /></button>
      </header>
      <ChatModeSwitch mode={mode} onChange={onMode} />
      <div className="chat-context">
        <span className="context-dot" style={selected && mode === 'local' ? { background: nodeColor(selected, theme) } : undefined} />
        <div>
          <strong>{mode === 'local' ? selected?.label ?? title : provider ? providerNames[provider.provider] : 'No provider connected'}</strong>
          <small>{mode === 'local' ? selected ? (roleLabel[selected.role] ?? selected.role) + (selected.section ? ' / Class ' + selected.section : '') : 'Choose a node' : provider?.model ?? 'API connection required'}</small>
        </div>
        {mode === 'assistant' && <button className="icon-button" type="button" aria-label="Graph assistant provider settings" title="Provider settings" onClick={onProvider}><Icon name="plug" /></button>}
      </div>
      <div className="chat-body" ref={body}>
        {unavailable && (
          <div className="chat-empty">
            <h3>Connect an AI provider</h3>
            <p>Explain connections, walk through message passing, or create and edit graphs from chat.</p>
            <button type="button" className="primary-button" onClick={onProvider}>Add provider <Icon name="arrow" /></button>
          </div>
        )}
        {!unavailable && thread.turns.length === 0 && !thread.pending && (
          <div className="chat-empty">
            <h3>{mode === 'local' ? 'Ask from this node' : 'Work with this graph'}</h3>
            {mode === 'local' && <p>{selected ? 'Questions follow the graph. Watch each handoff on the canvas.' : 'Select a node to inspect its information.'}</p>}
            <div className="chat-prompts" aria-label="Example prompts">
              {prompts.map(prompt => <button key={prompt.label} type="button" onClick={() => onSend(prompt.question)}>
                <span>{prompt.label}</span><Icon name="arrow" />
              </button>)}
            </div>
          </div>
        )}
        {thread.turns.length > 0 && <div className="turns" role="log" aria-label="Conversation">
          {thread.turns.map(turn => (
            <article className="turn" key={turn.id}>
              <p className="chat-question">{turn.question}</p>
              <div className="chat-answer">
                <p>{answerText(turn.answer)}</p>
                {(turn.source || turn.trace) && <div className="answer-meta">
                  {turn.source && <small>{turn.source}</small>}
                  {turn.trace && <button type="button" className="replay-button" onClick={() => onReplay(turn.trace!)} aria-label="Replay path on graph">
                    <Icon name="replay" /> Replay path <span>{
                      turn.trace.incoming ? 'Aggregation' : turn.trace.path.length === 2 ? '1 hop' : (turn.trace.path.length - 1) + ' hops'
                    }</span>
                  </button>}
                </div>}
                {turn.proposal && <ProposalCard proposal={turn.proposal} applied={turn.applied} onApply={() => onApply(turn)} />}
              </div>
            </article>
          ))}
        </div>}
        {thread.pending && <div className="turn pending-turn">
          <p className="chat-question">{thread.pending}</p>
          <p className="chat-pending" role="status">{mode === 'local' ? 'Checking the graph…' : 'Waiting for the provider…'}</p>
        </div>}
        {thread.error && <div className="chat-failure" role="alert">
          <p>{thread.error.message}</p>
          <button type="button" className="text-button" disabled={unavailable} onClick={() => onSend(thread.error!.question)}>Retry</button>
        </div>}
      </div>
      {library.length > 0 && <QuestionLibrary key={threadKey} questions={library} pending={!!thread.pending} onSend={onSend} />}
      {!unavailable && <form className="chat-form" onSubmit={send}>
        <label className="sr-only" htmlFor="question">Chat message</label>
        <input id="question" placeholder={mode === 'local' ? 'Ask a question…' : 'Explain or edit this graph…'}
          value={draft} maxLength={mode === 'local' ? 1000 : 1500} autoComplete="off" onChange={event => updateDraft(event.target.value)} />
        <button type="submit" className="send-button" aria-label="Send message" title="Send message" disabled={!draft.trim() || !!thread.pending}><Icon name="send" /></button>
      </form>}
    </aside>
  )
}
