import {
  forceCenter, forceCollide, forceLink, forceManyBody, forceSimulation, forceX, forceY,
} from 'd3-force'
import type { SimulationLinkDatum, SimulationNodeDatum } from 'd3-force'
import type { GraphNode, Workspace } from './school'

type Position = { x: number; y: number }

export interface PlottedNode extends GraphNode, SimulationNodeDatum {
  x: number
  y: number
  radius: number
  degree: number
  anchor: Position
}
export interface PlottedLink extends SimulationLinkDatum<PlottedNode> {
  source: PlottedNode
  target: PlottedNode
}

const radius: Record<string, number> = { Student: 3.1, CR: 5.5, 'In-charge': 4.2, HOD: 6.5, Dean: 7, Director: 8.5, Input: 6.5, Hidden: 8, Output: 7 }
const classCenters = [
  { x: -180, y: -225 }, { x: 225, y: -190 }, { x: 334, y: 65 },
  { x: 79, y: 226 }, { x: -295, y: 128 },
]

export function linkKey(source: string, target: string) {
  return source < target ? source + ':' + target : target + ':' + source
}

function ring(index: number, count: number, distance: number, rotation = -Math.PI / 2) {
  const angle = rotation + index * 2 * Math.PI / Math.max(1, count)
  return { x: Math.cos(angle) * distance, y: Math.sin(angle) * distance }
}

export function layoutGraph(graph: Workspace) {
  const sections = [...new Set(graph.nodes.flatMap(node => node.section ? [node.section] : []))].sort()
  const subjects = [...new Set(graph.nodes.filter(node => node.role === 'HOD').flatMap(node => node.subject ? [node.subject] : []))]
  const hasSchoolLayout = sections.length > 0 && subjects.length > 0
  const degree = new Map<string, number>()
  graph.links.forEach(({ source, target }) => {
    degree.set(source, (degree.get(source) ?? 0) + 1)
    degree.set(target, (degree.get(target) ?? 0) + 1)
  })
  const maxDegree = Math.max(1, ...degree.values())

  function schoolAnchor(node: GraphNode, index: number) {
    const classIndex = sections.indexOf(node.section ?? '')
    const subjectIndex = subjects.indexOf(node.subject ?? '')
    const cluster = sections.length === 5 && classIndex >= 0
      ? classCenters[classIndex] : ring(classIndex, sections.length, 270, -1.26)
    const department = ring(subjectIndex, subjects.length, 156, -.97)
    if (node.role === 'Director') return { x: 14, y: -79 }
    if (node.role === 'Dean') return { x: -25, y: 14 }
    if (node.role === 'HOD' && subjectIndex >= 0) return department
    if (node.role === 'CR' && classIndex >= 0) return cluster
    if (node.role === 'In-charge' && classIndex >= 0 && subjectIndex >= 0) {
      return { x: .51 * cluster.x + .54 * department.x, y: .51 * cluster.y + .54 * department.y }
    }
    if (classIndex >= 0) {
      const roll = node.roll ?? index
      const local = ring(roll * .382 + classIndex * .18, 1, 13 * Math.sqrt(Math.max(1, roll)), 0)
      return { x: cluster.x + local.x * 1.18, y: cluster.y + local.y * .78 }
    }
    return ring(index, graph.nodes.length, 120)
  }

  const nodes: PlottedNode[] = graph.nodes.map((node, index) => {
    const position = hasSchoolLayout ? schoolAnchor(node, index) :
      ring(index, graph.nodes.length, 65 + 150 * (1 - (degree.get(node.id) ?? 0) / maxDegree))
    const connections = degree.get(node.id) ?? 0
    return { ...node, ...position, anchor: position, degree: connections,
      radius: (radius[node.role] ?? 5.5) + Math.log2(Math.max(1, connections)) * 1.05 }
  })
  const byId = new Map(nodes.map(node => [node.id, node]))
  const links: PlottedLink[] = graph.links.flatMap(link => {
    const source = byId.get(link.source)
    const target = byId.get(link.target)
    return source && target ? [{ source, target }] : []
  })
  const linkForce = forceLink<PlottedNode, PlottedLink>(links)
    .strength(link => link.source.role === 'Student' ? .29 : .35)
  const xForce = forceX<PlottedNode>().strength(hasSchoolLayout ? .115 : .032)
  const yForce = forceY<PlottedNode>().strength(hasSchoolLayout ? .115 : .032)
  const simulation = forceSimulation(nodes).stop().alphaDecay(.032).velocityDecay(.36)
    .force('links', linkForce)
    .force('charge', forceManyBody().strength(hasSchoolLayout ? -36 : -110).distanceMax(260))
    .force('collide', forceCollide<PlottedNode>().radius(node => node.radius + (hasSchoolLayout ? 5 : 19)))
    .force('x', xForce)
    .force('y', yForce)
    .force('center', forceCenter(0, 0).strength(.025))

  function setSpacing(spacing: number) {
    linkForce.distance(link => {
      const leaf = link.source.roll ?? 1
      const distance = link.source.role === 'Student' ? 29 + (leaf * 23 % 69) : 99
      return distance * spacing
    })
    xForce.x(node => node.anchor.x * spacing)
    yForce.y(node => node.anchor.y * spacing)
  }

  setSpacing(1)
  simulation.tick(160)
  return { nodes, links, byId, simulation, setSpacing }
}
