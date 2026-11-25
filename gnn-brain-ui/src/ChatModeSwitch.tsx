import { useRef, useState } from 'react'
import type { CSSProperties, KeyboardEvent, PointerEvent } from 'react'
import type { Mode } from './ChatPanel'
import Icon from './Icon'

type Gesture = { id: number; start: number; dragging: boolean }

export default function ChatModeSwitch({ mode, onChange }: { mode: Mode; onChange: (mode: Mode) => void }) {
  const gesture = useRef<Gesture | null>(null)
  const suppressClick = useRef(false)
  const [offset, setOffset] = useState<number | null>(null)

  function pointerDown(event: PointerEvent<HTMLDivElement>) {
    if (!event.isPrimary || event.button !== 0) return
    suppressClick.current = false
    gesture.current = { id: event.pointerId, start: event.clientX, dragging: false }
  }

  function pointerMove(event: PointerEvent<HTMLDivElement>) {
    const drag = gesture.current
    if (!drag || drag.id !== event.pointerId) return
    if (!drag.dragging) {
      if (Math.abs(event.clientX - drag.start) < 6) return
      drag.dragging = true
      event.currentTarget.setPointerCapture(event.pointerId)
    }
    const bounds = event.currentTarget.getBoundingClientRect()
    const slot = (bounds.width - 8) / 2
    const ratio = (event.clientX - bounds.left - 4 - slot / 2) / slot
    setOffset(Math.max(-.07, Math.min(1.07, ratio)) * 100)
  }

  function finishPointer(event: PointerEvent<HTMLDivElement>) {
    const drag = gesture.current
    if (!drag || drag.id !== event.pointerId) return
    gesture.current = null
    if (!drag.dragging) return
    suppressClick.current = true
    setOffset(null)
    if (event.type === 'pointerup') {
      const { left, width } = event.currentTarget.getBoundingClientRect()
      onChange(event.clientX - left < width / 2 ? 'local' : 'assistant')
    }
  }

  function handleKeys(event: KeyboardEvent<HTMLDivElement>) {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
    event.preventDefault()
    const next = event.key === 'Home' ? 'local' : event.key === 'End' ? 'assistant' :
      mode === 'local' ? 'assistant' : 'local'
    event.currentTarget.querySelector<HTMLButtonElement>('[data-option="' + next + '"]')?.focus()
    onChange(next)
  }

  const style = offset === null ? undefined : { '--lens-position': offset + '%' } as CSSProperties
  return (
    <div className="chat-switch" role="group" aria-label="Chat mode" style={style} data-mode={mode}
      data-dragging={offset !== null || undefined} onKeyDown={handleKeys}
      onPointerDown={pointerDown} onPointerMove={pointerMove} onPointerUp={finishPointer}
      onPointerCancel={finishPointer} onLostPointerCapture={finishPointer}
      onPointerLeave={() => { if (!gesture.current?.dragging) gesture.current = null }}
      onClickCapture={event => {
        if (suppressClick.current && event.detail > 0) {
          suppressClick.current = false
          event.stopPropagation()
        }
      }}>
      <span className="chat-mode-lens" aria-hidden="true" />
      <button type="button" data-option="local" aria-pressed={mode === 'local'} onClick={() => onChange('local')}>
        <Icon name="network" /> Node chat
      </button>
      <button type="button" data-option="assistant" aria-pressed={mode === 'assistant'} onClick={() => onChange('assistant')}>
        <Icon name="spark" /> Graph assistant
      </button>
    </div>
  )
}
