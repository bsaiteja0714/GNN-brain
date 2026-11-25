import unittest

from app.graph.brain import bot_engine
from app.graph.knowledge import SCHOOL_RECORDS, SCHOOL_SCENARIOS


class SchoolRoutingTests(unittest.TestCase):
    def test_school_has_five_complete_class_reporting_chains(self):
        graph = bot_engine.graph_data()
        self.assertEqual([item["studentCount"] for item in graph["classes"]], [35] * 5)
        self.assertEqual(len(graph["nodes"]), 207)
        self.assertEqual(len(graph["links"]), 226)
        self.assertEqual(len({node["label"] for node in graph["nodes"]}), 207)
        for section in "ABCDE":
            with self.subTest(section=section):
                self.assertEqual(list(bot_engine.G.successors(f"S-{section}-1")), [f"CR-{section}"])
                self.assertEqual(len(list(bot_engine.G.successors(f"CR-{section}"))), 5)

    def test_owner_stops_forwarding_and_returns_via_same_edges(self):
        cases = (
            ("Where is morning assembly?", ["S-A-1", "CR-A"]),
            ("How soon is algebra homework due?", ["S-A-1", "CR-A", "incharge-A-math"]),
            ("Where is the chemistry practical?", ["S-A-1", "CR-A", "incharge-A-science"]),
            ("When is the coding workshop?", ["S-A-1", "CR-A", "incharge-A-computing", "hod-computing"]),
            ("When are soccer trials?", ["S-A-1", "CR-A", "incharge-A-sports", "hod-sports"]),
            ("Our classroom projector is broken.", ["S-A-1", "CR-A", "incharge-A-computing"]),
            ("When is Founders Day?", ["S-A-1", "CR-A", "incharge-A-science", "hod-science", "dean"]),
            ("What is the attendance policy?",
             ["S-A-1", "CR-A", "incharge-A-science", "hod-science", "dean", "director"]),
        )
        for question, route in cases:
            with self.subTest(question=question):
                result = bot_engine.chat("S-A-1", question)
                self.assertEqual(result["status"], "answered")
                self.assertEqual([step["node"] for step in result["route"]], route)
                self.assertEqual(result["record"]["node"], route[-1])
                self.assertEqual(result["returnPath"], route[::-1])

    def test_class_records_and_follow_ups_keep_their_scope(self):
        result = bot_engine.chat("S-E-2", "When is the maths assignment due?")
        self.assertIn("Class E", result["answer"])
        self.assertIn("6 December", result["answer"])
        first = bot_engine.chat("S-E-2", "When is Founders Day?")
        follow_up = bot_engine.chat("S-E-2", "Where is it?", first["context"])
        self.assertIn("main auditorium", follow_up["answer"])
        self.assertEqual(follow_up["context"], first["context"])
        self.assertEqual(bot_engine.chat("S-E-2", "Where is Class A assembly?")["status"], "clarify")
        self.assertEqual(bot_engine.chat("S-E-2", "Where is Class A’s assembly?")["status"], "clarify")

    def test_local_and_unanswered_questions(self):
        self.assertEqual(bot_engine.chat("S-A-1", "Who are you?")["status"], "local")
        self.assertEqual(bot_engine.chat("S-A-1", "When is this respective event in our college?")["status"], "clarify")
        self.assertEqual(bot_engine.chat("S-A-1", "Assembly and Founders Day")["status"], "clarify")
        missing = bot_engine.chat("S-A-1", "When is the chess tournament?")
        self.assertEqual(missing["status"], "unresolved")
        self.assertEqual(missing["route"][-1], {"node": "director", "status": "unresolved"})
        self.assertEqual(missing["returnPath"], [])
        self.assertIsNone(missing["record"])

    def test_leadership_conversation_starts_at_selected_node(self):
        result = bot_engine.chat("Dr. Vikram Rao", "When is Founders Day?")
        self.assertEqual(result["route"], [{"node": "dean", "status": "answered"}])
        self.assertEqual(result["returnPath"], ["dean"])

    def test_director_can_consult_the_dean_for_a_published_event(self):
        result = bot_engine.chat("director", "When is Founders Day?")
        self.assertEqual([step["node"] for step in result["route"]], ["director", "dean"])
        self.assertEqual(result["returnPath"], ["dean", "director"])

    def test_all_nodes_have_knowledge_and_every_listed_question_routes_to_its_role(self):
        self.assertEqual({record.owner for record in SCHOOL_RECORDS}, set(bot_engine.node_metadata))
        self.assertEqual(len({(record.owner, record.topic) for record in SCHOOL_RECORDS}), len(SCHOOL_RECORDS))
        for scenario in SCHOOL_SCENARIOS:
            with self.subTest(question=scenario["question"]):
                result = bot_engine.chat("S-A-1", scenario["question"])
                self.assertEqual(result["status"], "answered")
                source = result["record"]["node"]
                self.assertEqual(bot_engine.node_metadata[source].role, scenario["role"])
                if scenario.get("subject"):
                    self.assertEqual(bot_engine.node_metadata[source].subject, scenario["subject"])
                self.assertEqual(result["returnPath"], [step["node"] for step in reversed(result["route"])])

    def test_node_profiles_stay_with_the_selected_student(self):
        first = bot_engine.chat("S-A-1", "What are you working on?")
        second = bot_engine.chat("S-A-2", "What is your favorite subject?")
        self.assertIn("water cycle", first["answer"])
        self.assertIn("mathematics", second["answer"])
        self.assertEqual(first["returnPath"], ["S-A-1"])
        self.assertEqual(second["record"]["node"], "S-A-2")
        self.assertEqual(bot_engine.chat("dean", "What are you working on?")["status"], "clarify")

    def test_new_notices_respect_topic_scope_and_route(self):
        missed_exam = bot_engine.chat("S-A-1", "I was absent and missed my exam. What should I do?")
        self.assertEqual(missed_exam["record"]["node"], "dean")
        class_notes = bot_engine.chat("S-C-2", "Where are the shared notes?")
        self.assertEqual(class_notes["record"]["node"], "CR-C")
        password = bot_engine.chat("S-D-3", "I forgot my password for coding class")
        self.assertEqual(password["record"]["node"], "incharge-D-computing")
        self.assertEqual([step["node"] for step in password["route"]], ["S-D-3", "CR-D", "incharge-D-computing"])


if __name__ == "__main__":
    unittest.main()
