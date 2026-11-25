import {
  ArrowRight, ArrowUp, ChevronDown, Maximize, MessageSquare, Minus, Moon, Network, PanelRight,
  PlugZap, Plus, RotateCcw, Search, Settings2, Sparkles, Sun, X,
} from 'lucide-react'
import type { LucideProps } from 'lucide-react'

const icons = {
  plug: PlugZap, network: Network, close: X, chat: MessageSquare, search: Search,
  chevron: ChevronDown, plus: Plus, minus: Minus, fit: Maximize, send: ArrowUp,
  replay: RotateCcw, arrow: ArrowRight, panel: PanelRight, spark: Sparkles, settings: Settings2,
  sun: Sun, moon: Moon,
}

export default function Icon({ name, ...props }: LucideProps & { name: keyof typeof icons }) {
  const Glyph = icons[name]
  return <Glyph size={18} strokeWidth={1.75} aria-hidden="true" {...props} />
}
