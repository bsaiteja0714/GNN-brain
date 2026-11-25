"""Graph snapshots and checked provider-proposed operations."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

NodeId = Annotated[str, StringConstraints(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GraphNode(StrictModel):
    id: NodeId
    label: ShortText
    role: ShortText = "Node"
    text: str = Field(default="", max_length=1200)
    section: ShortText | None = None
    subject: ShortText | None = None
    roll: int | None = None


class GraphLink(StrictModel):
    source: NodeId
    target: NodeId

    def pair(self):
        return (self.source, self.target)


class Workspace(StrictModel):
    title: ShortText
    nodes: list[GraphNode] = Field(max_length=350)
    links: list[GraphLink] = Field(max_length=1400)

    @model_validator(mode="after")
    def check_graph(self):
        ids = {node.id for node in self.nodes}
        pairs = {link.pair() for link in self.links}
        if len(ids) != len(self.nodes):
            raise ValueError("Node IDs must be unique.")
        if len(pairs) != len(self.links):
            raise ValueError("Links must be unique.")
        if any(source not in ids or target not in ids or source == target for source, target in pairs):
            raise ValueError("Each link needs two different existing nodes.")
        return self


class Changes(StrictModel):
    mode: Literal["new", "edit"]
    title: ShortText | None = None
    upsertNodes: list[GraphNode] = Field(default_factory=list, max_length=100)
    removeNodes: list[NodeId] = Field(default_factory=list, max_length=100)
    addLinks: list[GraphLink] = Field(default_factory=list, max_length=300)
    removeLinks: list[GraphLink] = Field(default_factory=list, max_length=300)


class ModelReply(StrictModel):
    answer: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=8000)]
    path: list[NodeId] = Field(default_factory=list, max_length=30)
    proposal: Changes | None = None


def apply_changes(base: Workspace, changes: Changes):
    if changes.mode == "new":
        if not changes.title or not changes.upsertNodes or changes.removeNodes or changes.removeLinks:
            raise ValueError("A new graph needs a title and nodes and cannot remove existing items.")
        base = Workspace(title=changes.title, nodes=[], links=[])

    nodes = {node.id: node for node in base.nodes}
    links = {link.pair(): link for link in base.links}
    removed = set(changes.removeNodes)
    updated = {node.id: node for node in changes.upsertNodes}
    deleted_links = {link.pair() for link in changes.removeLinks}
    added_links = {link.pair(): link for link in changes.addLinks}

    if not removed <= nodes.keys() or not deleted_links <= links.keys():
        raise ValueError("A removal refers to a node or link that does not exist.")
    if (len(updated) != len(changes.upsertNodes) or len(added_links) != len(changes.addLinks)
            or len(removed) != len(changes.removeNodes) or len(deleted_links) != len(changes.removeLinks)
            or removed & updated.keys() or deleted_links & added_links.keys()):
        raise ValueError("The proposal repeats an operation or includes conflicting operations.")
    if added_links.keys() & links.keys():
        raise ValueError("The proposal adds a link that already exists.")

    additions = [node.label for node_id, node in updated.items() if node_id not in nodes]
    edits = [node.label for node_id, node in updated.items() if node_id in nodes and nodes[node_id] != node]
    removals = [node.label for node_id, node in nodes.items() if node_id in removed]
    retained_links = {pair: link for pair, link in links.items() if pair not in deleted_links and not (set(pair) & removed)}
    candidate = Workspace(
        title=changes.title or base.title,
        nodes=[node for node_id, node in (nodes | updated).items() if node_id not in removed],
        links=list((retained_links | added_links).values()),
    )
    if candidate == base or not candidate.nodes:
        raise ValueError("The proposal must produce a changed graph with at least one node.")
    return {
        "mode": changes.mode, "graph": candidate,
        "added": additions, "edited": edits, "removed": removals,
        "linksAdded": len(added_links), "linksRemoved": len(links) - len(retained_links),
    }


def checked_path(path, graph):
    ids = {node.id for node in graph.nodes}
    pairs = {frozenset(link.pair()) for link in graph.links}
    if len(path) != len(set(path)) or any(node not in ids for node in path):
        return []
    if any(frozenset((source, target)) not in pairs for source, target in zip(path, path[1:])):
        return []
    return path
