export type Theme = 'dark' | 'light'

export type GraphNode = {
  id: string
  label: string
  role: string
  text: string
  section?: string | null
  subject?: string | null
  roll?: number | null
}

export type GraphLink = { source: string; target: string }
export type Workspace = { title: string; nodes: GraphNode[]; links: GraphLink[] }

export type SchoolScenario = { label: string; question: string; role: string; subject?: string | null }

export type SchoolGraph = {
  nodes: GraphNode[]
  links: GraphLink[]
  classes: { id: string; label: string; studentCount: number }[]
  subjects: { id: string; label: string }[]
  scenarios: SchoolScenario[]
  defaultNode: string
  demo: boolean
}

export type SchoolReply = {
  answer: string
  status: 'answered' | 'unresolved' | 'clarify' | 'local'
  context: string | null
  route: { node: string }[]
  returnPath: string[]
  record: { title: string; reference: string; node: string } | null
}

export type Proposal = {
  mode: 'edit' | 'new'
  graph: Workspace
  added: string[]
  edited: string[]
  removed: string[]
  linksAdded: number
  linksRemoved: number
}

export type AssistantReply = { answer: string; path: string[]; proposal: Proposal | null }

export type Trace = { id: number; path: string[]; returning: string[]; source?: string; incoming?: string[] }
export type GraphPhase = { traceId: number; node: string; stage: 'ask' | 'return' | 'done'; step: number; total: number }

export const roleLabel: Record<string, string> = {
  CR: 'Class representative', 'In-charge': 'Subject in-charge', HOD: 'Head of department',
}

const darkRoles: Record<string, string> = {
  Student: '#a8a8a8', CR: '#ae98f3', 'In-charge': '#65b9a5', HOD: '#da88ad',
  Dean: '#efb46d', Director: '#e98b7f',
  Input: '#ae98f3', Hidden: '#efb46d', Output: '#65b9a5',
}

const lightRoles: Record<string, string> = {
  Student: '#61728e', CR: '#6554d3', 'In-charge': '#137b9e', HOD: '#8847ba',
  Dean: '#ab641f', Director: '#b84476', Input: '#576bc6', Hidden: '#8847ba', Output: '#1d8069',
}
const darkClasses: Record<string, string> = { A: '#b19aef', B: '#73c9c5', C: '#8cc581', D: '#df91a6', E: '#e4b570' }
const lightClasses: Record<string, string> = { A: '#725dd2', B: '#2484ad', C: '#248571', D: '#a34b82', E: '#a46e26' }

export function roleColor(role: string, theme: Theme) {
  return (theme === 'light' ? lightRoles : darkRoles)[role] ?? (theme === 'light' ? '#5e6584' : '#adadad')
}

export function nodeColor(node: GraphNode, theme: Theme) {
  const colors = theme === 'light' ? lightClasses : darkClasses
  return (node.role === 'Student' && node.section ? colors[node.section] : null) || roleColor(node.role, theme)
}

export const messagePassingGraph: Workspace = {
  title: 'Message passing example',
  nodes: [
    { id: 'sample-a', label: 'Paper A', role: 'Input', text: 'Example feature value 2. Linked to Topic.' },
    { id: 'sample-b', label: 'Paper B', role: 'Input', text: 'Example feature value 4. Linked to Topic.' },
    { id: 'sample-c', label: 'Paper C', role: 'Input', text: 'Example feature value 6. Linked to Topic.' },
    { id: 'sample-topic', label: 'Topic', role: 'Hidden', text: 'Pools the three incoming features. Mean aggregation gives (2 + 4 + 6) / 3 = 4.' },
    { id: 'sample-rep', label: 'Updated representation', role: 'Output', text: 'Receives the aggregate 4. A learned transformation could then combine it with the node’s own features.' },
  ],
  links: [
    { source: 'sample-a', target: 'sample-topic' },
    { source: 'sample-b', target: 'sample-topic' },
    { source: 'sample-c', target: 'sample-topic' },
    { source: 'sample-topic', target: 'sample-rep' },
  ],
}
