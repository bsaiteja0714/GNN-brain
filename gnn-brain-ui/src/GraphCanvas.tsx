import { useEffect, useMemo, useRef, useState } from 'react'
import type { KeyboardEvent, PointerEvent } from 'react'
import { layoutGraph, linkKey } from './graphLayout'
import type { PlottedNode } from './graphLayout'
import Icon from './Icon'
import { nodeColor } from './school'
import type { GraphNode, GraphPhase, Theme, Trace, Workspace } from './school'

type Props = {
  graph: Workspace
  selected: string | null
  trace?: Trace
  theme: Theme
  onSelect: (node: GraphNode) => void
  onPhase: (phase: GraphPhase) => void
}

type Point = { x: number; y: number }
type Gesture = { pointer: number; start: Point; last: Point; time: number; velocity: Point; node?: PlottedNode; dragged: boolean }
const defaults = { spacing: 1, labels: true, arrows: false, motion: true }
const STEP_MS = 380
const FRAME_MS = 1000 / 60
const LABEL_FONT = '"Instrument Sans Variable", "Segoe UI", sans-serif'
const graphPaint = {
  dark: {
    edge: '#b5b5b56b', muted: '#a8a8a852', subdued: '#a8a8a83e', focused: '#cbb6ff91',
    forward: '#c8a9ff', returning: '#75dac1', source: '#ffd18f',
    halo: '#1b1b1b', text: '#c7c7c7', strong: '#ebebeb', neighbor: '#dbdbdb', faint: '#9d9d9d',
  },
  light: {
    edge: '#506b9980', muted: '#526b9b62', subdued: '#526b9b45', focused: '#1769c49f',
    forward: '#2367c6', returning: '#0d8272', source: '#af6209',
    halo: '#e7eff9', text: '#263b58', strong: '#17253d', neighbor: '#1e4068', faint: '#506783',
  },
}
const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value))

function line(ctx: CanvasRenderingContext2D, source: Point, target: Point) {
  ctx.beginPath()
  ctx.moveTo(source.x, source.y)
  ctx.lineTo(target.x, target.y)
  ctx.stroke()
}

function circle(ctx: CanvasRenderingContext2D, x: number, y: number, radius: number) {
  ctx.beginPath()
  ctx.arc(x, y, radius, 0, Math.PI * 2)
}

function arrow(ctx: CanvasRenderingContext2D, from: Point, to: PlottedNode, zoom: number) {
  const dx = to.x - from.x
  const dy = to.y - from.y
  const length = Math.hypot(dx, dy)
  const size = 5 / zoom
  const offset = Math.max(to.radius, 2.8 / zoom) + 2 / zoom
  if (length < offset + size) return
  const x = dx / length, y = dy / length
  const tip = { x: to.x - x * offset, y: to.y - y * offset }
  ctx.beginPath()
  ctx.moveTo(tip.x - x * size + y * size * .5, tip.y - y * size - x * size * .5)
  ctx.lineTo(tip.x, tip.y)
  ctx.lineTo(tip.x - x * size - y * size * .5, tip.y - y * size + x * size * .5)
  ctx.stroke()
}

function graphLabel(node: PlottedNode, detail: boolean) {
  if (detail) return node.label
  if (node.role === 'CR') return 'Class ' + node.section
  if (node.role === 'HOD') return ({ science: 'Science', math: 'Mathematics', english: 'English', computing: 'Computing', sports: 'Physical Education' } as Record<string, string>)[node.subject ?? ''] ?? node.label
  if (node.role === 'Dean' || node.role === 'Director') return node.role
  return node.label
}

export default function GraphCanvas({ graph, selected, trace, theme, onSelect, onPhase }: Props) {
  const surface = useRef<HTMLCanvasElement>(null)
  const plot = useMemo(() => layoutGraph(graph), [graph])
  const camera = useRef({ x: 0, y: 0, zoom: 1, width: 0, height: 0, ratio: 1, manual: false })
  const cameraTarget = useRef<{ x: number; y: number; zoom: number } | null>(null)
  const focus = useRef({ selected, hover: '', trace, theme, onPhase })
  const gesture = useRef<Gesture | null>(null)
  const [display, setDisplay] = useState(defaults)
  const displayRef = useRef(defaults)
  const spacingPlot = useRef<typeof plot | null>(null)
  const refresh = useRef<() => void>(() => {})
  const fit = useRef<() => void>(() => {})
  const traceTime = useRef(0)

  useEffect(() => {
    Object.assign(focus.current, { selected, theme, onPhase })
    refresh.current()
  }, [selected, theme, onPhase])

  useEffect(() => {
    focus.current.trace = trace
    traceTime.current = performance.now()
    refresh.current()
  }, [trace])

  useEffect(() => {
    const canvas = surface.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return
    const view = camera.current
    const state = focus.current
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)')
    let frame = 0
    let lastPhase = ''
    let lastTick = 0
    let disposed = false
    let lastSelection = state.selected
    let selectionStarted = -1000

    function render(now: number) {
      frame = 0
      if (!ctx) return
      const target = cameraTarget.current
      if (target) {
        const settled = Math.abs(target.x - view.x) + Math.abs(target.y - view.y) < .35 &&
          Math.abs(target.zoom - view.zoom) < .001
        if (settled || reduced.matches) {
          Object.assign(view, target)
          cameraTarget.current = null
        } else {
          view.x += (target.x - view.x) * .26
          view.y += (target.y - view.y) * .26
          view.zoom += (target.zoom - view.zoom) * .26
        }
      }
      if (lastSelection !== state.selected) {
        lastSelection = state.selected
        selectionStarted = now
      }
      const selectionProgress = reduced.matches ? 1 : clamp((now - selectionStarted) / 150, 0, 1)
      const settings = displayRef.current
      const colors = graphPaint[state.theme]
      const simulation = plot.simulation
      const moving = settings.motion && !reduced.matches && simulation.alpha() > simulation.alphaMin()
      if (moving) {
        const elapsed = lastTick ? now - lastTick : FRAME_MS
        const ticks = Math.min(3, Math.floor((elapsed + .1) / FRAME_MS))
        if (ticks > 0) {
          simulation.tick(ticks)
          lastTick = now - Math.max(0, elapsed - ticks * FRAME_MS) % FRAME_MS
        }
      } else {
        lastTick = 0
      }
      const { x, y, zoom, width, height, ratio } = view
      const animation = state.trace
      const forward = animation?.path ?? []
      const backward = animation?.returning ?? []
      const forwardEdges = Math.max(0, forward.length - 1)
      const backwardEdges = Math.max(0, backward.length - 1)
      const forwardDuration = forwardEdges * STEP_MS
      const pause = backwardEdges ? 160 : 0
      const duration = forwardDuration + pause + backwardEdges * STEP_MS
      const elapsed = reduced.matches ? duration : Math.max(0, now - traceTime.current)
      const stage = elapsed >= duration ? 'done' : elapsed >= forwardDuration + pause ? 'return' : 'ask'
      const activePath = stage === 'return' ? backward : forward
      const elapsedStep = stage === 'return' ? (elapsed - forwardDuration - pause) / STEP_MS : elapsed / STEP_MS
      const index = clamp(Math.floor(elapsedStep), 0, Math.max(0, activePath.length - 1))
      const ratioStep = clamp(elapsedStep - index, 0, 1)
      const activeFrom = plot.byId.get(activePath[index])
      const activeTo = plot.byId.get(activePath[index + 1])
      const highlight = new Set(forward.slice(0, stage === 'ask' ? index + 1 : forward.length))
      const forwardLinks = new Set(forward.slice(1, stage === 'ask' ? index + 1 : forward.length)
        .map((node, offset) => linkKey(forward[offset], node)))
      for (const node of animation?.incoming ?? []) {
        highlight.add(node)
        if (stage !== 'ask' || index > 0) forwardLinks.add(linkKey(node, forward[1]))
      }
      const returned = new Set(stage === 'return' ? backward.slice(0, index + 1) : stage === 'done' ? backward : [])
      const returnLinks = new Set(backward.slice(1, stage === 'return' ? index + 1 : stage === 'done' ? backward.length : 0)
        .map((node, offset) => linkKey(backward[offset], node)))
      const neighborhood = new Set<string>()
      if (state.hover) {
        neighborhood.add(state.hover)
        for (const { source, target } of plot.links) {
          if (source.id === state.hover) neighborhood.add(target.id)
          if (target.id === state.hover) neighborhood.add(source.id)
        }
      }
      if (animation && forward.length) {
        const node = stage === 'done' ? backward.at(-1) ?? forward.at(-1)! : activePath[index]
        const phaseKey = [animation.id, stage, index].join(':')
        if (phaseKey !== lastPhase) {
          lastPhase = phaseKey
          state.onPhase({ traceId: animation.id, node, stage, step: index + 1, total: activePath.length })
        }
      }

      ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
      ctx.clearRect(0, 0, width, height)
      ctx.translate(width / 2 + x, height / 2 + y)
      ctx.scale(zoom, zoom)
      ctx.lineWidth = .9 / zoom
      ctx.strokeStyle = state.hover ? colors.subdued : forward.length ? colors.muted : colors.edge
      for (const edge of plot.links) {
        const touching = edge.source.id === state.hover || edge.target.id === state.hover
        if (touching) continue
        line(ctx, edge.source, edge.target)
        if (settings.arrows && zoom > .55 && !forwardLinks.has(linkKey(edge.source.id, edge.target.id))) {
          arrow(ctx, edge.source, edge.target, zoom)
        }
      }
      if (state.hover) {
        ctx.lineWidth = 1 / zoom
        ctx.strokeStyle = colors.focused
        for (const edge of plot.links) {
          if (edge.source.id !== state.hover && edge.target.id !== state.hover) continue
          line(ctx, edge.source, edge.target)
          if (settings.arrows) arrow(ctx, edge.source, edge.target, zoom)
        }
      }
      for (const edge of plot.links) {
        const key = linkKey(edge.source.id, edge.target.id)
        if (!forwardLinks.has(key)) continue
        const returning = returnLinks.has(key)
        ctx.strokeStyle = returning ? colors.returning : colors.forward
        ctx.lineWidth = 1.25 / zoom
        line(ctx, edge.source, edge.target)
        if (settings.arrows) {
          const path = returning ? backward : forward
          const reverse = path.includes(edge.source.id) && path.includes(edge.target.id) && path.indexOf(edge.source.id) > path.indexOf(edge.target.id)
          arrow(ctx, reverse ? edge.target : edge.source, reverse ? edge.source : edge.target, zoom)
        }
      }

      const pulses: Point[] = []
      const drawProgress = (start: Point, target: Point) => {
        const color = stage === 'return' ? colors.returning : colors.forward
        const pulse = { x: start.x + (target.x - start.x) * ratioStep, y: start.y + (target.y - start.y) * ratioStep }
        pulses.push(pulse)
        ctx.strokeStyle = color
        ctx.lineWidth = 1.5 / zoom
        line(ctx, start, pulse)
      }
      if (stage !== 'done' && activeFrom && activeTo) {
        drawProgress(activeFrom, activeTo)
        if (stage === 'ask' && index === 0) {
          for (const id of animation?.incoming ?? []) {
            const contributor = plot.byId.get(id)
            if (contributor) drawProgress(contributor, activeTo)
          }
        }
      }

      const labels: { node: PlottedNode; strong: boolean; detail: boolean; neighbor: boolean }[] = []
      for (const node of plot.nodes) {
        const emphasized = highlight.has(node.id)
        const selectedNode = node.id === state.selected
        const picked = selectedNode || node.id === state.hover
        const neighbor = neighborhood.has(node.id)
        const source = animation?.source === node.id && emphasized
        const color = source ? colors.source : returned.has(node.id) ? colors.returning :
          emphasized ? colors.forward : nodeColor(node, state.theme)
        const nodeRadius = Math.max(node.radius, (node.role === 'Student' ? 2.65 : 4.5) / zoom)
        if (picked || emphasized) {
          ctx.strokeStyle = color
          ctx.globalAlpha = selectedNode ? .45 + .5 * selectionProgress : picked ? .75 : .62
          ctx.lineWidth = (selectedNode ? 1.55 : 1.1) / zoom
          circle(ctx, node.x, node.y, nodeRadius + (selectedNode ? 4 + (1 - selectionProgress) * 3 : 3.5) / zoom)
          ctx.stroke()
        }
        ctx.globalAlpha = picked || emphasized || neighbor ? 1 : neighborhood.size ? .54 : forward.length ? .66 : .93
        ctx.fillStyle = color
        circle(ctx, node.x, node.y, nodeRadius)
        ctx.fill()
        ctx.shadowBlur = 0
        ctx.globalAlpha = 1
        const major = !['Student', 'In-charge'].includes(node.role)
        const focusedNeighbor = neighbor && (node.role !== 'Student' || zoom > 1.15 || neighborhood.size <= 8)
        if (picked || emphasized || (settings.labels && (focusedNeighbor || major || zoom > 1.65))) {
          labels.push({ node, strong: picked || emphasized, detail: picked || emphasized || focusedNeighbor || zoom > 1.4, neighbor })
        }
      }

      if (pulses.length) {
        ctx.fillStyle = stage === 'return' ? colors.returning : colors.forward
        ctx.shadowColor = ctx.fillStyle
        ctx.shadowBlur = 0
        for (const pulse of pulses) {
          circle(ctx, pulse.x, pulse.y, 2.8 / zoom)
          ctx.fill()
        }
        ctx.shadowBlur = 0
      }

      const placed: { left: number; top: number; right: number; bottom: number }[] = []
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      labels.sort((a, b) => Number(b.strong) - Number(a.strong) || Number(b.neighbor) - Number(a.neighbor))
      for (const { node, strong, detail, neighbor } of labels) {
        const size = (strong ? 13 : 12) / zoom
        ctx.font = (strong ? '450 ' : '400 ') + size + 'px ' + LABEL_FONT
        const label = graphLabel(node, detail)
        const textWidth = ctx.measureText(label).width
        const gap = Math.max(node.radius, 4 / zoom) + 6 / zoom
        const side = gap + textWidth / 2
        const spots = [{ x: node.x, y: node.y + gap }]
        if (strong || node.role === 'HOD' || node.role === 'CR') spots.push(
          { x: node.x, y: node.y - gap - size },
          { x: node.x + side, y: node.y - size / 2 },
          { x: node.x - side, y: node.y - size / 2 },
        )
        const bounds = ({ x, y }: Point) => ({
          left: x - textWidth / 2 - 3 / zoom, right: x + textWidth / 2 + 3 / zoom,
          top: y - 2 / zoom, bottom: y + size + 3 / zoom,
        })
        const position = spots.find(point => {
          const box = bounds(point)
          return placed.every(item => box.left >= item.right || box.right <= item.left || box.top >= item.bottom || box.bottom <= item.top)
        }) ?? (strong ? spots[0] : undefined)
        if (!position) continue
        placed.push(bounds(position))
        ctx.lineWidth = 2.6 / zoom
        ctx.strokeStyle = colors.halo
        ctx.lineJoin = 'round'
        ctx.strokeText(label, position.x, position.y)
        ctx.fillStyle = strong ? colors.strong : neighbor ? colors.neighbor :
          neighborhood.size || forward.length ? colors.faint : colors.text
        ctx.fillText(label, position.x, position.y)
      }
      if (moving || cameraTarget.current || selectionProgress < 1 || (stage !== 'done' && animation)) schedule()
    }

    function schedule() {
      if (!frame && !disposed) frame = requestAnimationFrame(render)
    }

    function fitPlot() {
      view.manual = false
      cameraTarget.current = null
      if (!plot.nodes.length) {
        Object.assign(view, { x: 0, y: 0, zoom: 1 })
        schedule()
        return
      }
      const xs = plot.nodes.map(node => node.x)
      const ys = plot.nodes.map(node => node.y)
      const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys)
      const paddingX = view.width < 440 ? 57 : 112
      const paddingY = view.height < 460 ? 120 : 138
      const spanX = maxX - minX
      const spanY = maxY - minY
      const previousFit = Math.min((view.width - paddingX) / (spanX + 39), (view.height - paddingY) / (spanY + 39))
      const safeFit = Math.min((view.width - 26) / (spanX + 28), (view.height - 93) / (spanY + 26))
      view.zoom = clamp(Math.min(previousFit * 1.25, safeFit), .15, 1.75)
      view.x = -(minX + maxX) * view.zoom / 2
      view.y = -(minY + maxY) * view.zoom / 2 + 16
      schedule()
    }

    function resize() {
      if (!canvas) return
      const { width, height } = canvas.getBoundingClientRect()
      if (!width || !height) return
      const ratio = Math.min(window.devicePixelRatio || 1, 2)
      Object.assign(view, { width, height, ratio })
      canvas.width = Math.round(width * ratio)
      canvas.height = Math.round(height * ratio)
      if (!view.manual) fitPlot()
      cancelAnimationFrame(frame)
      render(performance.now())
    }

    function wheel(event: WheelEvent) {
      event.preventDefault()
      if (!canvas) return
      const box = canvas.getBoundingClientRect()
      const x = event.clientX - box.left - view.width / 2
      const y = event.clientY - box.top - view.height / 2
      const base = cameraTarget.current ?? view
      const next = clamp(base.zoom * Math.exp(-event.deltaY * .00155), .15, 5)
      const delta = next / base.zoom
      cameraTarget.current = { x: x - (x - base.x) * delta, y: y - (y - base.y) * delta, zoom: next }
      view.manual = true
      schedule()
    }

    refresh.current = schedule
    fit.current = fitPlot
    view.manual = false
    state.hover = ''
    resize()
    const observer = new ResizeObserver(resize)
    observer.observe(canvas)
    canvas.addEventListener('wheel', wheel, { passive: false })
    void document.fonts.load('400 12px ' + LABEL_FONT).then(schedule, schedule)
    return () => {
      disposed = true
      cancelAnimationFrame(frame)
      observer.disconnect()
      canvas.removeEventListener('wheel', wheel)
    }
  }, [plot])

  useEffect(() => {
    const changed = displayRef.current.spacing !== display.spacing ||
      (spacingPlot.current !== plot && display.spacing !== 1)
    displayRef.current = display
    spacingPlot.current = plot
    if (changed) {
      plot.setSpacing(display.spacing)
      plot.simulation.alpha(.68)
      if (!display.motion || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        plot.simulation.tick(160)
        fit.current()
      }
    }
    if (!display.motion) plot.simulation.alpha(0)
    refresh.current()
  }, [display, plot])

  function localPoint(event: PointerEvent<HTMLCanvasElement>): Point {
    const bounds = event.currentTarget.getBoundingClientRect()
    return { x: event.clientX - bounds.left, y: event.clientY - bounds.top }
  }

  function findNode(point: Point) {
    const view = camera.current
    const x = (point.x - view.width / 2 - view.x) / view.zoom
    const y = (point.y - view.height / 2 - view.y) / view.zoom
    let closest: PlottedNode | undefined
    let distance = Infinity
    for (const node of plot.nodes) {
      const current = Math.hypot(x - node.x, y - node.y)
      if (current < distance && current <= Math.max(node.radius, 5 / view.zoom) + 3 / view.zoom) {
        closest = node
        distance = current
      }
    }
    return closest
  }

  function pointerDown(event: PointerEvent<HTMLCanvasElement>) {
    if (!event.isPrimary || event.button !== 0) return
    const point = localPoint(event)
    cameraTarget.current = null
    gesture.current = { pointer: event.pointerId, start: point, last: point, time: event.timeStamp,
      velocity: { x: 0, y: 0 }, node: findNode(point), dragged: false }
    event.currentTarget.setPointerCapture(event.pointerId)
  }

  function pointerMove(event: PointerEvent<HTMLCanvasElement>) {
    if (!event.isPrimary) return
    const point = localPoint(event)
    const drag = gesture.current
    if (drag?.pointer === event.pointerId) {
      drag.dragged ||= Math.hypot(point.x - drag.start.x, point.y - drag.start.y) > 4
      if (!drag.dragged) return
      const view = camera.current
      view.manual = true
      const delta = { x: point.x - drag.last.x, y: point.y - drag.last.y }
      if (drag.node) {
        const node = drag.node
        node.fx = node.x += delta.x / view.zoom
        node.fy = node.y += delta.y / view.zoom
        const scale = FRAME_MS / (Math.max(4, event.timeStamp - drag.time) * view.zoom)
        drag.velocity = { x: clamp(delta.x * scale, -19, 19), y: clamp(delta.y * scale, -19, 19) }
        focus.current.hover = node.id
        plot.simulation.alpha(Math.max(.45, plot.simulation.alpha()))
      } else {
        const base = cameraTarget.current ?? view
        cameraTarget.current = { x: base.x + delta.x, y: base.y + delta.y, zoom: base.zoom }
      }
      drag.last = point
      drag.time = event.timeStamp
      event.currentTarget.style.cursor = 'grabbing'
    } else {
      const found = findNode(point)
      focus.current.hover = found?.id ?? ''
      event.currentTarget.style.cursor = found ? 'pointer' : 'grab'
    }
    refresh.current()
  }

  function pointerUp(event: PointerEvent<HTMLCanvasElement>) {
    const drag = gesture.current
    if (drag?.pointer !== event.pointerId) return
    gesture.current = null
    if (drag.node && drag.dragged) {
      const node = drag.node
      const release = event.type === 'pointerup' && event.timeStamp - drag.time < 95
      node.fx = node.fy = null
      node.vx = release ? drag.velocity.x : 0
      node.vy = release ? drag.velocity.y : 0
      plot.simulation.alpha(Math.max(.3, plot.simulation.alpha()))
    }
    if (drag.node && !drag.dragged && event.type === 'pointerup') onSelect(drag.node)
    focus.current.hover = findNode(localPoint(event))?.id ?? ''
    event.currentTarget.style.cursor = 'grab'
    refresh.current()
  }

  function zoomBy(factor: number) {
    const view = camera.current
    const base = cameraTarget.current ?? view
    const next = clamp(base.zoom * factor, .15, 5)
    cameraTarget.current = { x: base.x * next / base.zoom, y: base.y * next / base.zoom, zoom: next }
    view.manual = true
    refresh.current()
  }

  function handleKeys(event: KeyboardEvent<HTMLCanvasElement>) {
    if (event.key === '+' || event.key === '=') zoomBy(1.25)
    else if (event.key === '-') zoomBy(.8)
    else if (event.key === '0') fit.current()
    else {
      const direction: Record<string, Point> = {
        ArrowLeft: { x: 1, y: 0 }, ArrowRight: { x: -1, y: 0 },
        ArrowUp: { x: 0, y: 1 }, ArrowDown: { x: 0, y: -1 },
      }
      const move = direction[event.key]
      if (!move) return
      const view = camera.current
      const step = event.shiftKey ? 90 : 30
      const base = cameraTarget.current ?? view
      cameraTarget.current = { x: base.x + move.x * step, y: base.y + move.y * step, zoom: base.zoom }
      view.manual = true
      refresh.current()
    }
    event.preventDefault()
  }

  return (
    <>
      <canvas ref={surface} className="graph-canvas" tabIndex={0} aria-label="Interactive graph. Drag nodes or the canvas. Use Find a node to select via keyboard. Arrow keys pan, plus and minus zoom, zero fits."
        onKeyDown={handleKeys} onPointerDown={pointerDown} onPointerMove={pointerMove}
        onPointerUp={pointerUp} onPointerCancel={pointerUp} onLostPointerCapture={pointerUp}
        onPointerLeave={() => { focus.current.hover = ''; refresh.current() }} />
      <details className="graph-settings" onKeyDown={event => {
        if (event.key === 'Escape') {
          event.currentTarget.open = false
          event.currentTarget.querySelector('summary')?.focus()
        }
      }}>
        <summary title="Graph settings" aria-label="Graph settings"><Icon name="settings" /></summary>
        <form className="graph-settings-panel" aria-label="Graph display settings" onSubmit={event => event.preventDefault()}>
          <div><strong>Graph display</strong><button type="button" onClick={() => setDisplay(defaults)}>Reset</button></div>
          <label className="graph-range"><span>Connection spacing</span><output>{Math.round(display.spacing * 100)}%</output>
            <input type="range" min=".65" max="1.45" step=".05" value={display.spacing} onChange={event => {
              setDisplay(current => ({ ...current, spacing: Number(event.target.value) }))
            }} />
          </label>
          <label>Overview labels<input type="checkbox" checked={display.labels} onChange={event => setDisplay(current => ({ ...current, labels: event.target.checked }))} /></label>
          <label>Link arrows<input type="checkbox" checked={display.arrows} onChange={event => setDisplay(current => ({ ...current, arrows: event.target.checked }))} /></label>
          <label>Node motion<input type="checkbox" checked={display.motion} onChange={event => setDisplay(current => ({ ...current, motion: event.target.checked }))} /></label>
        </form>
      </details>
      <div className="graph-tools" aria-label="Graph controls">
        <button type="button" title="Zoom in" aria-label="Zoom in" onClick={() => zoomBy(1.3)}><Icon name="plus" /></button>
        <button type="button" title="Zoom out" aria-label="Zoom out" onClick={() => zoomBy(1 / 1.3)}><Icon name="minus" /></button>
        <button type="button" title="Fit graph" aria-label="Fit graph" onClick={() => fit.current()}><Icon name="fit" /></button>
      </div>
    </>
  )
}
