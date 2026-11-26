"""Intent detection for local chat and the provider-backed assistant."""

import re
from difflib import SequenceMatcher

GRAPH_TERMS = re.compile(
    r"\b(graph|nodes?|edges?|links?|neighbors?|neighbours?|gnn|aggregation|message passing|"
    r"reporting|hierarchy|class(?:room)?|school|campus|cr|hod|dean|director|teacher|students?|"
    r"assembly|timetable|exam|assignment|library|tournament|workshop|attendance|sports|trip|"
    r"permission slip|club|bus|id card|subject|route|policy|librarian|principal)\b"
)
REFERENCE = re.compile(
    r"^(?:(?:and )?(?:what|when|where|who|why|how|can|could|is|are|does|do|will)\b.*"
    r"\b(it|that|there|then|they|those|the same|you mean|the venue)\b)|"
    r"^(?:and )?(?:when|where|who|why|how|what time|what about|can you (?:explain|elaborate)|"
    r"tell me more|more details|go on|explain this|explain that|show me more)$"
)
LEAD_IN = re.compile(r"^(?:hi|hey|hello|good (?:morning|afternoon|evening)|thanks(?: so much)?|thank you)[!,.:;–—-]+\s*", re.I)
VAGUE = re.compile(r"^(?:please )?(?:can you |could you )?(?:help(?: me)?|i need help)(?: with (?:this|that|school|the graph))?$")
REQUEST = re.compile(r"\b(what|when|where|who|how|why|which|can|could|do|does|is|are|show|explain|"
                     r"find|list|tell|give|add|remove|delete|edit|rename|change|connect|create|generate|build|"
                     r"missed|lost|broke|broken|forgot|need)\b")
SOCIAL_FILLER = set("hi hey hello there everyone friend good morning afternoon evening yo well how are you doing today going whats up it is thank thanks so much a lot very really i appreciate your help that this helped helpful was great awesome cool perfect nice okay ok got understand makes sense goodbye bye see later take care and for you too im fine glad to hear yes no have been hope all".split())
GREETINGS = ("hi", "hey", "hello")


def compact(message):
    return " ".join(re.findall(r"[a-z0-9]+", message.casefold().replace("’", "'").replace("'", "")))


def classify(message, *, matched=False, previous_graph=False):
    text = compact(message)
    if VAGUE.fullmatch(text):
        return "clarify"
    if matched or (GRAPH_TERMS.search(text) and REQUEST.search(text)):
        return "graph"
    if text and set(text.split()) <= SOCIAL_FILLER:
        if re.search(r"\b(thanks?|appreciate|helpful|helped|got it|makes sense|great|awesome|perfect|nice)\b", text) or text in {"ok", "okay", "yes", "no", "cool"}:
            return "acknowledgement"
        if re.search(r"\b(how are you|hows it going|whats up|how you doing|how have you been|hope you are well)\b", text):
            return "check-in"
        if re.search(r"\b(bye|goodbye|see you|take care)\b", text):
            return "farewell"
        if re.search(r"\b(hi|hey|hello|morning|afternoon|evening|yo)\b", text):
            return "greeting"
    if 2 <= len(text) <= 6 and text.isalpha() and any(
        SequenceMatcher(None, text, greeting).ratio() >= .8 for greeting in GREETINGS
    ):
        return "greeting"
    if previous_graph and REFERENCE.search(text):
        return "follow-up"
    return "general"


def social_reply(intent, *, name=None, has_history=False):
    if intent == "greeting":
        if has_history:
            return "Hey again. What would you like to look at next?"
        return f"Hi, I’m {name}. What can I help you with?" if name else "Hi! What are you curious about?"
    if intent == "check-in":
        return "I’m doing well, thanks for asking. How can I help?"
    if intent == "acknowledgement":
        return "You’re welcome. Happy to keep going if you have another question." if has_history else "Of course. What can I help you with?"
    if intent == "farewell":
        return "See you next time!"
    return None


def without_lead_in(message):
    return LEAD_IN.sub("", message, count=1).strip() or message
