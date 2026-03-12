import re
import random

# ─── Intent Detection ─────────────────────────────────────────────────────────

def detect_intent(question: str) -> str:
    q = question.lower().strip()
    # Greetings / casual small talk — check first
    greetings = ["hi", "hello", "hey", "hii", "heyy", "howdy", "sup", "yo",
                 "good morning", "good afternoon", "good evening",
                 "how are you", "how r u", "how's it going", "what's up",
                 "nice to meet", "greetings", "namaste", "salut"]
    if any(q == g or q.startswith(g) for g in greetings):
        return "greeting"
    # Check specific intents first before broad ones
    if any(w in q for w in ["concern", "worry", "worried", "problem", "issue", "stress"]):
        return "concerns"
    if any(w in q for w in ["interest", "passion", "passionate", "like", "love", "enjoy", "good at", "speciali"]):
        return "interests"
    if any(w in q for w in ["project", "working on", "building", "develop", "creat"]):
        return "projects"
    if any(w in q for w in ["mentor", "guide", "supervis", "who teach", "who is teach"]):
        return "mentor"
    if any(w in q for w in ["connect", "path", "reach", "report to", "talk to", "linked"]):
        return "connections"
    if any(w in q for w in ["student", "who is working", "who work", "members", "who is in"]):
        return "students"
    if any(w in q for w in ["who are you", "tell me about", "describe", "what is", "who is"]):
        return "describe"
    return "general"


# ─── Node Extraction ──────────────────────────────────────────────────────────

def extract_by_type(nodes_info: list, node_type: str) -> list[str]:
    result = []
    for entry in nodes_info:
        m = re.match(r"^(.+?)\s+\((.+?)\)$", entry.strip())
        if m and m.group(2).lower() == node_type.lower():
            result.append(m.group(1).strip())
    return result


def all_labels(nodes_info: list) -> list[str]:
    labels = []
    for entry in nodes_info:
        m = re.match(r"^(.+?)\s+\(", entry.strip())
        if m:
            labels.append(m.group(1).strip())
    return labels


# ─── Natural Language Joiners ─────────────────────────────────────────────────

def join_names(names: list[str], bold=True) -> str:
    if not names:
        return ""
    fmt = [f"**{n}**" for n in names] if bold else names
    if len(fmt) == 1:
        return fmt[0]
    return ", ".join(fmt[:-1]) + " and " + fmt[-1]


# ─── In-Character Greeting ───────────────────────────────────────────────────

def greeting_response(subject: str, node_type: str, node_text: str) -> str:
    """Generate a warm, in-character greeting based on the node's role and data."""
    import re as _re

    # Extract interesting tidbits from node text
    concern = ""
    interest = ""
    project = ""
    m = _re.search(r"worried about ([^.]+)", node_text, _re.IGNORECASE)
    if m:
        concern = m.group(1).strip()
    m = _re.search(r"passionate about ([^.]+)", node_text, _re.IGNORECASE)
    if m:
        interest = m.group(1).strip()
    m = _re.search(r"working on the project\s+([a-zA-Z0-9_]+)", node_text, _re.IGNORECASE)
    if m:
        project = m.group(1).replace("_", " ").title()
    m = _re.search(r"I teach ([^.]+)", node_text, _re.IGNORECASE)
    teach = m.group(1).strip() if m else ""
    m = _re.search(r"mentor the project\s+([a-zA-Z0-9_]+)", node_text, _re.IGNORECASE)
    mentor_proj = m.group(1).replace("_", " ").title() if m else ""

    role_lower = node_type.lower()

    if role_lower == "student":
        parts = [f"Hey! I'm **{subject}**, a student here."]
        if interest:
            parts.append(f"I'm really into **{interest}**.")
        if project:
            parts.append(f"Right now I'm working on the **{project}** project.")
        if concern:
            parts.append(f"Honestly, I'm a bit stressed about **{concern}** these days.")
        parts.append("Feel free to ask me anything!")
        return " ".join(parts)

    elif role_lower == "teacher":
        parts = [f"Hello! I'm **{subject}**, a class teacher."]
        if teach:
            parts.append(f"I teach **{teach}** and love helping students grow.")
        if mentor_proj:
            parts.append(f"I'm currently mentoring the **{mentor_proj}** project.")
        parts.append("What would you like to know?")
        return " ".join(parts)

    elif role_lower == "cr":
        parts = [f"Hi there! I'm **{subject}**, the Class Representative."]
        if interest:
            parts.append(f"I'm passionate about **{interest}** and leadership.")
        parts.append("I act as the bridge between students and teachers. What's up?")
        return " ".join(parts)

    elif role_lower == "hod":
        return (
            f"Hello! I'm **{subject}**, Head of Department. "
            f"I oversee faculty, curriculum, and department decisions. "
            f"How can I assist you today?"
        )

    elif role_lower == "dean":
        return (
            f"Good day! I'm **{subject}**, the institute Dean. "
            f"I handle strategic vision, accreditation, and research funding. "
            f"Please ask me what you'd like to know."
        )

    elif role_lower == "admin":
        return (
            f"Hi! I'm **{subject}**. "
            f"I handle administrative matters at the institute. "
            f"How can I help you today?"
        )

    elif role_lower == "project":
        return (
            f"Hey! This is the **{subject}** project node. "
            f"I represent an ongoing student/faculty project in the graph. "
            f"Ask me who's working on me or who's mentoring this project!"
        )

    # Fallback
    return (
        f"Hello! I'm **{subject}**. "
        f"Click on me and ask anything — I'll answer based on the graph data I carry!"
    )


# ─── Main Answer Generator ────────────────────────────────────────────────────

def generate_answer(
    sender_label: str,
    relevant_nodes_info: list,
    paths_context: list,
    question: str,
    selected_node_context: str = "",
    node_metadata: dict | None = None,
    sender_node_id: str | None = None,
) -> str:

    intent  = detect_intent(question)
    subject = sender_label.strip() if sender_label else "this node"
    node_text = ""
    node_type = ""

    if node_metadata and sender_node_id:
        meta = node_metadata.get(sender_node_id, {})
        node_text = meta.get("text", "")
        node_type = meta.get("type", "")

    # ── Greeting — respond in character immediately ──────────────────────────
    if intent == "greeting":
        return greeting_response(subject, node_type, node_text)

    projects = extract_by_type(relevant_nodes_info, "project")
    teachers = extract_by_type(relevant_nodes_info, "Teacher")
    students = extract_by_type(relevant_nodes_info, "Student")
    crs      = extract_by_type(relevant_nodes_info, "CR")
    labels   = all_labels(relevant_nodes_info)

    # ── Projects ────────────────────────────────────────────────────────────

    if intent == "projects":
        # Try getting project directly from the node's own text
        if node_text:
            m = re.search(r"working on the project\s+([a-zA-Z0-9_]+)", node_text, re.IGNORECASE)
            if m:
                proj_raw = m.group(1).replace("_", " ").title()
                openers = [
                    f"Right now, **{subject}** is working on the **{proj_raw}** project.",
                    f"**{subject}** is currently involved in the **{proj_raw}** project.",
                    f"Based on the graph data, **{subject}** is working on **{proj_raw}**.",
                ]
                return random.choice(openers)

        if projects:
            proj_str = join_names(projects)
            if len(projects) == 1:
                return f"**{subject}** is currently working on the {proj_str} project."
            return (
                f"**{subject}** is involved in {len(projects)} projects: {proj_str}. "
                f"It looks like they have a pretty full plate!"
            )

        # Fall back: check if subject itself is a project node
        if node_type == "project":
            if teachers:
                return (
                    f"The **{subject}** project is being mentored by {join_names(teachers)}. "
                    f"Students connected to this project can reach them through the graph."
                )
            return (
                f"**{subject}** is a project in the system. "
                f"I don't have details on who is currently working on it yet."
            )

        return (
            f"I don't have specific project data for **{subject}** yet. "
            f"Try clicking on a student node and asking again — the graph links students directly to their projects."
        )

    # ── Mentor ──────────────────────────────────────────────────────────────

    if intent == "mentor":
        if node_text:
            m = re.search(r"mentor[a-z\s]*project[:\s]+([a-zA-Z0-9_]+)", node_text, re.IGNORECASE)
            if m:
                proj_raw = m.group(1).replace("_", " ").title()
                return f"**{subject}** is actively mentoring the **{proj_raw}** project."

        if teachers:
            return (
                f"This project is being guided by {join_names(teachers)}. "
                f"They are responsible for mentoring and overseeing its progress."
            )
        if node_type == "project" and not teachers:
            return f"The **{subject}** project doesn't seem to have a mentor assigned yet in the graph."

        return f"I couldn't find mentoring information for **{subject}** in the current graph data."

    # ── Students ─────────────────────────────────────────────────────────────

    if intent == "students":
        if students:
            return (
                f"The following students are connected to **{subject}**: {join_names(students)}. "
                f"They are part of the same section or project cluster."
            )
        if crs:
            return (
                f"**{subject}**'s section is represented by {join_names(crs)}. "
                f"The CR handles communication between students and the teacher."
            )
        return f"I don't see any students directly linked to **{subject}** in the graph right now."

    # ── Connections / Path ────────────────────────────────────────────────────

    if intent == "connections":
        if paths_context:
            path_lines = "\n".join(f"• {p}" for p in paths_context[:5])
            return (
                f"Here's how **{subject}** connects to the rest of the graph:\n\n"
                f"{path_lines}"
            )
        if labels:
            return (
                f"**{subject}** is directly connected to {join_names(labels[:5])}. "
                f"You can explore further connections by clicking on those nodes."
            )
        return f"**{subject}** doesn't appear to have visible connections in the current graph."

    # ── Concerns ─────────────────────────────────────────────────────────────

    if intent == "concerns":
        if node_text:
            m = re.search(r"worried about ([^.]+)", node_text, re.IGNORECASE)
            if m:
                concern = m.group(1).strip()
                return (
                    f"**{subject}** is currently concerned about **{concern}**. "
                    f"This is reflected in their connections within the graph — "
                    f"they may be linked to nodes that can help address this."
                )
        return (
            f"I don't have specific concern data for **{subject}**. "
            f"Try selecting a student node and asking about their worries."
        )

    # ── Interests ─────────────────────────────────────────────────────────────

    if intent == "interests":
        if node_text:
            m = re.search(r"passionate about ([^.]+)", node_text, re.IGNORECASE)
            if m:
                interest = m.group(1).strip()
                return f"**{subject}** is passionate about **{interest}**. That shapes how they connect with others in the graph."

            m = re.search(r"I teach ([^.]+)", node_text, re.IGNORECASE)
            if m:
                subject_taught = m.group(1).strip()
                return f"**{subject}** teaches **{subject_taught}** and mentors students in that area."

        return f"I don't have detail about **{subject}**'s specific interests in the graph data yet."

    # ── Describe ──────────────────────────────────────────────────────────────

    if intent == "describe":
        if node_text:
            # Clean up the first-person intro
            clean = re.sub(r"^I am ", "", node_text).strip()
            clean = re.sub(r"\s+", " ", clean)
            return f"Here's what I know about **{subject}**: {clean}"
        if labels:
            return (
                f"**{subject}** is connected to {join_names(labels[:5])} in the graph. "
                f"Select the node and explore its neighbours for more details."
            )
        return f"I don't have a detailed description for **{subject}** yet."

    # ── General / Fallback ────────────────────────────────────────────────────

    if labels:
        return (
            f"Based on the graph, **{subject}** is connected to {join_names(labels[:4])}. "
            f"Could you ask something more specific, like their projects, interests, or connections?"
        )

    return (
        f"I don't have enough graph data to answer that about **{subject}** right now. "
        f"Try asking about their projects, concerns, or who they're connected to."
    )
