import { useEffect, useMemo, useRef, useState } from 'react'
import type { CSSProperties, PointerEvent } from 'react'
import ChatPanel from './ChatPanel'
import type { Mode, Thread, Turn } from './ChatPanel'
import GraphCanvas from './GraphCanvas'
import Icon from './Icon'
import ProviderDialog from './ProviderDialog'
import { post, providerNames } from './api'
import type { Provider } from './api'
import { messagePassingGraph, nodeColor, roleColor, roleLabel } from './school'
import type { AssistantReply, GraphNode, GraphPhase, SchoolGraph, SchoolReply, Theme, Trace, Workspace } from './school'
import './App.css'

type SavedWorkspace = { id: string; graph: Workspace }
const STORAGE = 'gnn-brain.workspaces.v1'
const ACTIVE = 'gnn-brain.active-workspace.v1'
const THEME = 'gnn-brain.theme.v1'
const DRAWER_WIDTH = 'gnn-brain.drawer-width.v1'
const MIN_DRAWER = 310
const MAX_DRAWER = 720
const ASSISTANT_PROMPTS = [
  { label: 'Explain this graph', question: 'Explain what the nodes and links represent in this graph and how information moves through it. Show one example path.' },
  { label: 'How does a GNN learn?', question: 'Use this graph to explain a GNN message-passing layer, neighborhood aggregation, and what weights are learned. Show an example path.' },
  { label: 'Generate a new graph', question: 'Create a new teaching graph with 8–12 nodes for a research citation network. Use roles for papers, authors, and topics and give each node a short description. Explain how a GNN could use it.' },
]
const LEARNING_QUESTION = 'How does mean aggregation work here?'

function initialWorkspaces(): SavedWorkspace[] {
  try {
    const stored: unknown = JSON.parse(localStorage.getItem(STORAGE) || '[]')
    if (!Array.isArray(stored)) return []
    return stored.filter(item => typeof item?.id === 'string' && typeof item.graph?.title === 'string'
      && Array.isArray(item.graph.nodes) && Array.isArray(item.graph.links))
  } catch {
    return []
  }
}

function initialWorkspace() {
  try { return localStorage.getItem(ACTIVE) ?? 'school' } catch { return 'school' }
}

function saveActive(id: string) {
  try { localStorage.setItem(ACTIVE, id) } catch { /* The workspace still works in memory. */ }
}

function App() {
  const [theme, setTheme] = useState<Theme>(() => {
    try { return localStorage.getItem(THEME) === 'light' ? 'light' : 'dark' } catch { return 'dark' }
  })
  const [school, setSchool] = useState<SchoolGraph>()
  const [saved, setSaved] = useState(initialWorkspaces)
  const [workspaceId, setWorkspaceId] = useState(initialWorkspace)
  const [selectedIds, setSelectedIds] = useState<Record<string, string>>({})
  const [threads, setThreads] = useState<Record<string, Thread>>({})
  const [mode, setMode] = useState<Mode>('local')
  const [chatOpen, setChatOpen] = useState(true)
  const [preferredWidth, setPreferredWidth] = useState(() => {
    try { return Number(localStorage.getItem(DRAWER_WIDTH)) || 0 } catch { return 0 }
  })
  const [availableWidth, setAvailableWidth] = useState(0)
  const [resizing, setResizing] = useState(false)
  const [provider, setProvider] = useState<Provider | null>(null)
  const [providerOpen, setProviderOpen] = useState(false)
  const [loadError, setLoadError] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const [storageNote, setStorageNote] = useState('')
  const [search, setSearch] = useState('')
  const [searchOpen, setSearchOpen] = useState(false)
  const [phase, setPhase] = useState<GraphPhase>()
  const [replay, setReplay] = useState<{ thread: string; trace: Trace }>()
  const [hiddenTrace, setHiddenTrace] = useState<number>()
  const nextId = useRef(0)
  const inFlight = useRef(new Set<string>())
  const bases = useRef(new Map<number, Workspace>())
  const workspaceMenu = useRef<HTMLDetailsElement>(null)
  const chatToggle = useRef<HTMLButtonElement>(null)
  const workbench = useRef<HTMLElement>(null)
  const drawer = useRef<HTMLDivElement>(null)
  const resizeDrag = useRef<{ pointer: number; start: number; width: number } | null>(null)
  const lastWidth = useRef(0)

  useEffect(() => {
    const element = workbench.current
    if (!element) return
    const observer = new ResizeObserver(([entry]) => setAvailableWidth(entry.contentRect.width))
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/graph', { signal: controller.signal })
      .then(response => {
        if (!response.ok) throw new Error('Graph unavailable')
        return response.json() as Promise<SchoolGraph>
      })
      .then(data => setSchool(data))
      .catch(() => { if (!controller.signal.aborted) setLoadError(true) })
    return () => controller.abort()
  }, [attempt])

  const demo = useMemo(() => school ? { title: 'School graph', nodes: school.nodes, links: school.links } : undefined, [school])
  const isSchool = workspaceId === 'school'
  const isSample = workspaceId === 'sample'
  const workspace = isSchool ? demo : isSample ? messagePassingGraph : saved.find(item => item.id === workspaceId)?.graph ?? demo
  const nodes = workspace?.nodes ?? []
  const selectedId = selectedIds[workspaceId] ?? (isSchool ? school?.defaultNode : nodes[0]?.id)
  const selected = nodes.find(node => node.id === selectedId)
  const threadKey = [workspaceId, mode, mode === 'local' ? selected?.id : 'graph'].join(':')
  const thread = threads[threadKey] ?? { turns: [] }
  const activeTrace = thread.pending ? undefined : replay?.thread === threadKey ? replay.trace : thread.turns.at(-1)?.trace
  const trace = activeTrace?.id === hiddenTrace ? undefined : activeTrace
  const term = search.trim().toLocaleLowerCase()
  const searchResults = term ? nodes.filter(node => [node.label, node.id, node.role, node.section && 'Class ' + node.section, node.subject]
    .some(value => value?.toLocaleLowerCase().includes(term))).slice(0, 9) : []
  const phaseNode = trace && phase?.traceId === trace.id ? nodes.find(node => node.id === phase.node) : undefined
  const source = nodes.find(node => node.id === trace?.source)
  const scenarios = school?.scenarios ?? []
  const rolePrompts = selected && selected.role !== 'Student'
    ? scenarios.filter(scenario => scenario.role === selected.role && (!selected.subject || scenario.subject === selected.subject))
    : []
  const prompts = mode === 'assistant' ? ASSISTANT_PROMPTS
    : isSchool ? (rolePrompts.length ? rolePrompts : scenarios).slice(0, 4)
      : isSample ? [{ label: 'Try mean aggregation', question: LEARNING_QUESTION }]
        : [{ label: 'Show this node’s neighbors', question: 'What are the neighbors of this node?' }]
  const maxDrawer = Math.max(MIN_DRAWER, Math.min(MAX_DRAWER, Math.floor(availableWidth) - 340))
  const drawerWidth = Math.min(maxDrawer, Math.max(MIN_DRAWER, preferredWidth || Math.min(390, availableWidth * .28)))

  function changeDrawerWidth(width: number, persist = false) {
    const next = Math.round(Math.min(maxDrawer, Math.max(MIN_DRAWER, width)))
    lastWidth.current = next
    setPreferredWidth(next)
    if (persist) {
      try { localStorage.setItem(DRAWER_WIDTH, String(next)) } catch { /* Keep the width for this session. */ }
    }
  }

  function startResize(event: PointerEvent<HTMLDivElement>) {
    if (event.button !== 0 || !event.isPrimary) return
    const width = Math.round(drawer.current?.querySelector('.chat-panel')?.getBoundingClientRect().width ?? drawerWidth)
    lastWidth.current = width
    resizeDrag.current = { pointer: event.pointerId, start: event.clientX, width }
    event.currentTarget.setPointerCapture(event.pointerId)
    setResizing(true)
  }

  function finishResize(event: PointerEvent<HTMLDivElement>) {
    if (resizeDrag.current?.pointer !== event.pointerId) return
    resizeDrag.current = null
    setResizing(false)
    changeDrawerWidth(lastWidth.current, true)
  }

  function updateThread(key: string, update: (current: Thread) => Thread) {
    setThreads(current => ({ ...current, [key]: update(current[key] ?? { turns: [] }) }))
  }

  function selectNode(node: GraphNode) {
    setSelectedIds(current => ({ ...current, [workspaceId]: node.id }))
    setReplay(undefined)
    setChatOpen(true)
    setSearch('')
    setSearchOpen(false)
  }

  function switchTheme() {
    const next = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    try { localStorage.setItem(THEME, next) } catch { /* The current tab still uses the selected theme. */ }
  }

  function switchWorkspace(id: string) {
    setWorkspaceId(id)
    saveActive(id)
    setSearch('')
    setSearchOpen(false)
    setReplay(undefined)
    workspaceMenu.current?.removeAttribute('open')
  }

  function persist(items: SavedWorkspace[]) {
    setSaved(items)
    try {
      localStorage.setItem(STORAGE, JSON.stringify(items))
      setStorageNote('')
    } catch {
      setStorageNote('Browser storage is full or unavailable. New changes are in this tab only.')
    }
  }

  function addWorkspace(graph: Workspace) {
    const id = crypto.randomUUID()
    persist([...saved, { id, graph }])
    switchWorkspace(id)
    setChatOpen(true)
    return id
  }

  function newWorkspace() {
    addWorkspace({ title: 'Untitled graph', nodes: [], links: [] })
    setMode('assistant')
  }

  async function send(question: string) {
    if (!workspace || inFlight.current.has(threadKey) || (mode === 'assistant' && !provider)) return
    const id = ++nextId.current
    inFlight.current.add(threadKey)
    setReplay(undefined)
    updateThread(threadKey, current => ({ turns: current.turns, pending: question }))

    try {
      let turn: Turn
      if (mode === 'assistant' && provider) {
        const history = thread.turns.slice(-4).flatMap(item => [
          { role: 'user', content: item.question }, { role: 'assistant', content: item.answer },
        ])
        const result = await post<AssistantReply>('/assistant', {
          provider: provider.provider, model: provider.model, query: question,
          graph: isSchool ? null : workspace, selected: selected?.id ?? null, history,
        }, AbortSignal.timeout(85_000), provider.key)
        if (result.proposal) bases.current.set(id, workspace)
        turn = { id, question, answer: result.answer, proposal: result.proposal, source: providerNames[provider.provider],
          trace: result.path.length > 1 ? { id, path: result.path, returning: [] } : undefined }
      } else if (isSample && question === LEARNING_QUESTION) {
        turn = { id, question,
          answer: 'Topic receives feature values 2, 4, and 6 from three neighbors. Their mean is (2 + 4 + 6) / 3 = 4. A GNN can then combine this aggregate with Topic’s own features and apply a learned transformation.',
          trace: { id, path: ['sample-a', 'sample-topic', 'sample-rep'], returning: [], incoming: ['sample-b', 'sample-c'] } }
      } else {
        const result = await post<SchoolReply>('/chat', {
          node: selected?.id, query: question, graph: isSchool ? undefined : workspace,
          previousQuestion: thread.turns.slice().reverse().find(item => item.context)?.context,
          history: thread.turns.slice(-8).map(({ question, answer, context }) => ({ question, answer, context })),
          provider: provider ? { provider: provider.provider, model: provider.model } : undefined,
        }, AbortSignal.timeout(provider ? 85_000 : 15_000), provider?.key)
        turn = { id, question, answer: result.answer, context: result.context, source: result.record?.reference,
          trace: result.route.length > 1 ? { id, path: result.route.map(step => step.node), returning: result.returnPath, source: result.record?.node } : undefined }
      }
      updateThread(threadKey, current => ({ turns: [...current.turns, turn] }))
    } catch (failure) {
      updateThread(threadKey, current => ({ turns: current.turns,
        error: { message: failure instanceof Error ? failure.message : 'Could not send the message.', question } }))
    } finally {
      inFlight.current.delete(threadKey)
    }
  }

  function apply(turn: Turn) {
    if (!turn.proposal || bases.current.get(turn.id) !== workspace || turn.applied) return false
    bases.current.delete(turn.id)
    const graph = turn.proposal.graph
    if (turn.proposal.mode === 'new' || isSchool || isSample) {
      const copy = turn.proposal.mode === 'edit' && graph.title === workspace?.title ? { ...graph, title: graph.title + ' (edited)' } : graph
      const id = addWorkspace(copy)
      updateThread(id + ':assistant:graph', () => ({ turns: [{ ...turn, trace: undefined, applied: true }] }))
    } else {
      persist(saved.map(item => item.id === workspaceId ? { ...item, graph } : item))
      if (selected && !graph.nodes.some(node => node.id === selected.id)) {
        setSelectedIds(current => ({ ...current, [workspaceId]: graph.nodes[0].id }))
      }
    }
    updateThread(threadKey, current => ({ ...current,
      turns: current.turns.map(item => item.id === turn.id ? { ...item, applied: true } : item) }))
    setReplay(undefined)
    if (activeTrace) setHiddenTrace(activeTrace.id)
    return true
  }

  const traceLabel = phaseNode && phase ? phase.stage === 'done'
    ? source ? 'Answer from ' + source.label : 'Path highlighted'
    : phase.stage === 'return' ? 'Returning through ' + phaseNode.label
      : trace?.incoming ? phase.step === 1 ? 'Aggregating neighbor features' : 'Updating representation'
        : 'Checking ' + phaseNode.label : ''

  return (
    <div className="app-shell" data-theme={theme}>
      <header className="topbar">
        <div className="topbar-start">
          <button type="button" className={'provider-trigger icon-button' + (provider ? ' connected' : '')}
            aria-label="AI provider settings" title={provider ? providerNames[provider.provider] + ' connected' : 'Add AI provider'}
            onClick={() => setProviderOpen(true)}><Icon name="plug" /></button>
          <span className="wordmark">GNN Brain</span>
          <span className="header-divider" />
          <details className="workspace-menu" ref={workspaceMenu}>
            <summary><Icon name="network" /><span>{workspace?.title ?? 'School graph'}</span><Icon name="chevron" /></summary>
            <div className="workspace-list">
              <button type="button" onClick={() => switchWorkspace('school')} aria-current={isSchool ? 'true' : undefined}>School graph</button>
              <button type="button" onClick={() => switchWorkspace('sample')} aria-current={isSample ? 'true' : undefined}>Message passing example</button>
              {saved.map(item => <button key={item.id} type="button" onClick={() => switchWorkspace(item.id)}
                aria-current={workspaceId === item.id ? 'true' : undefined}>{item.graph.title}</button>)}
              <button type="button" className="create-workspace" onClick={newWorkspace}><Icon name="plus" /> New graph</button>
            </div>
          </details>
        </div>
        <div className="topbar-actions">
          <button type="button" className="theme-toggle icon-button" onClick={switchTheme}
            aria-label={theme === 'dark' ? 'Switch to Light Studio' : 'Switch to Dark Glass'}
            title={theme === 'dark' ? 'Switch to Light Studio' : 'Switch to Dark Glass'}>
            <Icon name={theme === 'dark' ? 'sun' : 'moon'} />
          </button>
          <button type="button" ref={chatToggle} className={'chat-toggle' + (chatOpen ? ' pressed' : '')} aria-expanded={chatOpen}
            onClick={() => setChatOpen(value => !value)}><Icon name="chat" /><span>Chat</span></button>
        </div>
      </header>

      <main ref={workbench} className={'workbench' + (chatOpen ? ' with-chat' : '') + (resizing ? ' resizing-chat' : '')}
        style={preferredWidth ? { '--drawer-width': drawerWidth + 'px' } as CSSProperties : undefined}>
        <section className="graph-workspace" aria-label="Graph workspace">
          {workspace && <GraphCanvas graph={workspace} selected={selected?.id ?? null} trace={trace}
            theme={theme} onSelect={selectNode} onPhase={setPhase} />}
          <div className="graph-find" onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget)) setSearchOpen(false) }}>
            <div className="find-field"><Icon name="search" /><input type="search" aria-label="Find a node" placeholder="Find a node…"
              value={search} onFocus={() => setSearchOpen(true)} onChange={event => { setSearch(event.target.value); setSearchOpen(true) }}
              onKeyDown={event => {
                if (event.key === 'Escape') setSearchOpen(false)
                if (event.key === 'Enter' && searchResults[0]) selectNode(searchResults[0])
              }} /></div>
            {searchOpen && term && <div className="find-results">
              {searchResults.map(node => <button key={node.id} type="button" onClick={() => selectNode(node)}>
                <i style={{ background: nodeColor(node, theme) }} /><span>{node.label}</span><small>{node.role}{node.section ? ' / ' + node.section : ''}</small>
              </button>)}
              {!searchResults.length && <p>No matching nodes</p>}
            </div>}
          </div>

          {trace && phaseNode && <div className={'trace-status phase-' + phase!.stage} role="status">
            <i />
            <span>{traceLabel}</span>
            {phase!.stage !== 'done' && <small>{phase!.step}/{phase!.total}</small>}
            <button type="button" className="icon-button" aria-label="Clear highlighted path" onClick={() => setHiddenTrace(trace.id)}><Icon name="close" /></button>
          </div>}

          {(!workspace || !nodes.length) && <div className="graph-empty">
            <Icon name="network" />
            <h1>{loadError && !workspace ? 'School graph unavailable' : workspace ? 'Your graph is empty' : 'Loading school graph'}</h1>
            {loadError && !workspace ? <button type="button" className="quiet-button" onClick={() => { setLoadError(false); setAttempt(value => value + 1) }}>Try again</button>
              : workspace ? <button type="button" className="quiet-button" onClick={() => { setMode('assistant'); setChatOpen(true) }}>Create nodes with the assistant <Icon name="arrow" /></button> : null}
          </div>}

          {workspace && <footer className="graph-info">
            <span>{nodes.length} nodes <b>·</b> {workspace.links.length} links</span>
            {isSchool && <div className="graph-legend" aria-label="Node roles">
              {['Student', 'CR', 'In-charge', 'HOD', 'Dean', 'Director'].map(role =>
                <span key={role} title={roleLabel[role] ?? role}><i style={{ background: roleColor(role, theme) }} />{role}</span>)}
            </div>}
            {storageNote && <small role="status">{storageNote}</small>}
          </footer>}
        </section>

        <div className="chat-dock" ref={drawer} inert={!chatOpen} aria-hidden={!chatOpen}>
        <div className="chat-resize-handle" role="separator" aria-label="Chat panel width"
          aria-orientation="vertical" aria-valuemin={MIN_DRAWER} aria-valuemax={maxDrawer}
          aria-valuenow={drawerWidth} tabIndex={chatOpen ? 0 : -1}
          onPointerDown={startResize}
          onPointerMove={event => {
            const drag = resizeDrag.current
            if (drag?.pointer === event.pointerId) changeDrawerWidth(drag.width + drag.start - event.clientX)
          }}
          onPointerUp={finishResize} onPointerCancel={finishResize} onLostPointerCapture={finishResize}
          onKeyDown={event => {
            const width = { ArrowLeft: drawerWidth + 24, ArrowRight: drawerWidth - 24, Home: MIN_DRAWER, End: maxDrawer }[event.key]
            if (width === undefined) return
            event.preventDefault()
            changeDrawerWidth(width, true)
          }} />
        <ChatPanel hidden={!chatOpen} threadKey={threadKey} mode={mode} theme={theme}
          title={workspace?.title ?? 'School graph'} selected={selected}
          provider={provider} prompts={prompts} library={isSchool && mode === 'local' ? scenarios : []}
          thread={thread} onMode={setMode} onClose={() => { chatToggle.current?.focus(); setChatOpen(false) }}
          onProvider={() => setProviderOpen(true)} onSend={send} onApply={apply} onReplay={item => {
            setReplay({ thread: threadKey, trace: { ...item, id: ++nextId.current } })
          }} />
        </div>
      </main>
      {providerOpen && <ProviderDialog current={provider} onClose={() => setProviderOpen(false)}
        onConnect={connection => { setProvider(connection); setProviderOpen(false); setMode('assistant'); setChatOpen(true) }}
        onDisconnect={() => { setProvider(null); setProviderOpen(false) }} />}
    </div>
  )
}

export default App
