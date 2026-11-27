import json
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.api.assistant import (AssistantRequest, Connection, ConversationPlan, ask_assistant,
                               gemini_body, gemini_content, provider_request, verify_connection)
from app.api.chat import ChatRequest, chat_endpoint
from app.graph.workspace import Changes, Workspace, apply_changes, checked_path

BASE = Workspace(title="Example", nodes=[{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
                 links=[{"source": "a", "target": "b"}])


class GraphAssistantTests(unittest.TestCase):
    @patch("app.api.assistant.provider_request")
    def test_ambiguous_student_edit_accepts_null_lookup_fields_and_stops_at_clarification(self, call):
        call.return_value = {"action": "clarify", "answer": "Which class?", "query": None, "topic": None}
        request = AssistantRequest(provider="gemini", model="gemini-test", selected="S-A-1",
                                   query="Create a new student node named Avery Example in a class.")
        self.assertEqual(ask_assistant(request, "test-key"), {"answer": "Which class?", "path": [], "proposal": None})
        call.assert_called_once()
        self.assertIs(call.call_args.kwargs["schema"], ConversationPlan)

    def test_gemini_plan_schema_and_truncation(self):
        generation = gemini_body([], 1800, ConversationPlan)["generationConfig"]
        self.assertFalse(generation["responseJsonSchema"]["additionalProperties"])
        self.assertEqual(generation["responseJsonSchema"]["required"], ["action"])
        with self.assertRaisesRegex(HTTPException, "before completing"):
            gemini_content({"candidates": [{"finishReason": "MAX_TOKENS"}]})

    @patch("app.api.assistant.provider_request")
    def test_invalid_graph_link_is_rejected_after_valid_plan_and_reply(self, call):
        call.side_effect = [{"action": "graph", "answer": None, "query": None, "topic": None}, {
            "answer": "Prepared a proposal.",
            "proposal": {"mode": "edit", "addLinks": [{"source": "a", "target": "unknown"}]},
        }]
        request = AssistantRequest(provider="gemini", model="gemini-test", graph=BASE, query="Connect a to unknown")
        with self.assertRaisesRegex(HTTPException, "graph integrity validation"):
            ask_assistant(request, "test-key")
        self.assertEqual(len(BASE.links), 1)

    @patch("app.api.assistant.provider_request")
    def test_invalid_graph_response_is_distinct_from_an_invalid_proposal(self, call):
        call.side_effect = [{"action": "graph"}, {"answer": None}]
        request = AssistantRequest(provider="gemini", model="gemini-test", graph=BASE, query="Explain the graph")
        with self.assertRaises(HTTPException) as failure:
            ask_assistant(request, "test-key")
        self.assertEqual(failure.exception.status_code, 502)
        self.assertEqual(failure.exception.detail, "The provider returned an invalid graph response.")

    @patch("app.api.assistant.provider_request")
    def test_gemini_lookup_with_null_plan_answer_keeps_source_and_return_path(self, call):
        call.side_effect = [
            {"action": "lookup", "answer": None, "query": "When is Founders Day?", "topic": "founders-day"},
            {"answer": "Founders Day is on 11 December 2026."},
        ]
        result = chat_endpoint(ChatRequest(node="S-A-1", query="When is Founders Day?",
                                           provider=Connection(provider="gemini", model="gemini-test")), "test-key")
        self.assertEqual(result["answer"], "Founders Day is on 11 December 2026.")
        self.assertEqual(result["record"]["node"], "dean")
        self.assertEqual(result["returnPath"], [step["node"] for step in reversed(result["route"])])
        self.assertEqual(call.call_count, 2)

    @patch("app.api.assistant.provider_request")
    def test_invalid_evidence_rephrase_keeps_the_original_record_answer(self, call):
        question = "When is Founders Day?"
        expected = chat_endpoint(ChatRequest(node="S-A-1", query=question))
        request = ChatRequest(node="S-A-1", query=question, provider=Connection(provider="gemini", model="gemini-test"))
        for reply in ({"answer": "  "}, {"answer": "Unvalidated", "path": []}):
            with self.subTest(reply=reply):
                call.side_effect = [{"action": "lookup", "topic": "founders-day"}, reply]
                result = chat_endpoint(request, "test-key")
                for field in ("answer", "record", "returnPath"):
                    self.assertEqual(result[field], expected[field])

    @patch("app.api.assistant.provider_request")
    def test_reply_and_clarify_still_require_answer_text(self, call):
        request = AssistantRequest(provider="gemini", model="gemini-test", query="Hello")
        for action in ("reply", "clarify"):
            with self.subTest(action=action):
                call.return_value = {"action": action, "answer": None}
                with self.assertRaises(HTTPException) as error:
                    ask_assistant(request, "test-key")
                self.assertEqual(error.exception.detail, "The provider did not return an answer.")

    @patch("app.api.assistant.provider_request")
    def test_social_turn_uses_provider_without_traversal(self, call):
        call.return_value = {"action": "reply", "answer": "Doing well, thanks!"}
        request = AssistantRequest(provider="openai", model="test", query="Hey! How are you?")
        self.assertEqual(ask_assistant(request, "test-key"), {"answer": "Doing well, thanks!", "path": [], "proposal": None})
        call.assert_called_once()

    @patch("app.api.assistant.provider_request")
    def test_general_question_does_not_send_graph_or_use_a_returned_path(self, call):
        call.return_value = {"action": "reply", "answer": "Paris."}
        request = AssistantRequest(provider="openai", model="test", query="What is the capital of France?")
        self.assertEqual(ask_assistant(request, "test-key")["path"], [])
        self.assertFalse(any("Graph snapshot" in item["content"] for item in call.call_args.args[2]))

    def test_edit_is_validated_without_mutating_original(self):
        result = apply_changes(BASE, Changes(mode="edit", removeNodes=["b"],
                                             upsertNodes=[{"id": "c", "label": "C"}],
                                             addLinks=[{"source": "a", "target": "c"}]))
        self.assertEqual([node.id for node in result["graph"].nodes], ["a", "c"])
        self.assertEqual((result["added"], result["removed"], result["linksRemoved"]), (["C"], ["B"], 1))
        self.assertEqual([node.id for node in BASE.nodes], ["a", "b"])

        with self.assertRaises(ValueError):
            apply_changes(BASE, Changes(mode="edit", addLinks=[{"source": "a", "target": "missing"}]))
        with self.assertRaises(ValueError):
            apply_changes(BASE, Changes(mode="edit", upsertNodes=[
                {"id": "a", "label": "One"}, {"id": "a", "label": "Two"}]))

    def test_create_starts_with_empty_graph(self):
        result = apply_changes(BASE, Changes(mode="new", title="Study graph",
                                             upsertNodes=[{"id": "first", "label": "First"}]))
        self.assertEqual([node.id for node in result["graph"].nodes], ["first"])
        self.assertEqual(result["linksRemoved"], 0)

    def test_route_is_checked_against_actual_links(self):
        self.assertEqual(checked_path(["b", "a"], BASE), ["b", "a"])
        self.assertEqual(checked_path(["b", "missing"], BASE), [])
        self.assertEqual(checked_path(["a", "b", "a"], BASE), [])

    @patch("app.api.assistant.provider_request")
    def test_assistant_receives_whole_school_and_returns_validated_proposal(self, call):
        call.side_effect = [{"action": "graph", "answer": None}, {"answer": "Here is a new example.", "path": ["director", "dean"], "proposal": {
            "mode": "new", "title": "Test graph",
            "upsertNodes": [{"id": "input", "label": "Input"}, {"id": "output", "label": "Output"}],
            "addLinks": [{"source": "input", "target": "output"}],
        }}]
        result = ask_assistant(AssistantRequest(provider="openai", model="test", query="Create a graph",
                                               selected="S-A-1"), "test-key")
        _, _, messages, _ = call.call_args.args
        context = json.loads(messages[1]["content"].split("\n", 1)[1])
        self.assertEqual(len(context["graph"]["nodes"]), 207)
        self.assertEqual(len(context["graph"]["links"]), 226)
        records = context["publicDemoRecords"]
        self.assertTrue(any(record["title"] == "Library hours" for record in records))
        self.assertEqual([record["owner"] for record in records if record["reference"] == "Fictional student profile"], ["S-A-1"])
        self.assertEqual(result["path"], ["director", "dean"])
        self.assertEqual(result["proposal"]["graph"].title, "Test graph")

    @patch("app.api.assistant.provider_request")
    def test_implicit_lookup_returns_actual_route_and_uses_evidence(self, call):
        call.side_effect = [
            {"action": "lookup", "topic": "student-id", "query": "How do I replace my lost student ID?"},
            {"answer": "The front office can give you a temporary pass."},
        ]
        request = AssistantRequest(provider="openai", model="test", query="my badge is gone", selected="S-C-2")
        result = ask_assistant(request, "test-key")
        self.assertEqual(result["path"][0], "S-C-2")
        self.assertEqual(result["path"][-1], "director")
        _, _, messages, _ = call.call_args.args
        self.assertIn("front office", messages[1]["content"])

    @patch("app.api.assistant.provider_request")
    def test_connection_check_sends_no_graph(self, call):
        call.return_value = {"connected": True}
        self.assertEqual(verify_connection(Connection(provider="groq", model="test"), "test-key"), {"connected": True})
        self.assertEqual(call.call_args.args[2][-1]["content"], "Verify connection.")

    @patch("app.api.assistant.HTTPSConnection")
    def test_provider_request_uses_the_fixed_host_and_authorization_header(self, connect):
        connection = connect.return_value
        connection.getresponse.return_value.status = 200
        connection.getresponse.return_value.read.return_value = json.dumps({"choices": [
            {"message": {"content": '{"connected":true}'}},
        ]}).encode()
        result = provider_request(Connection(provider="openai", model="test"), "test-key", [], 512)
        self.assertEqual(result, {"connected": True})
        connect.assert_called_once_with("api.openai.com", timeout=40)
        method, path, payload, headers = connection.request.call_args.args
        self.assertEqual((method, path), ("POST", "/v1/chat/completions"))
        self.assertEqual(headers["Authorization"], "Bearer test-key")
        self.assertFalse(json.loads(payload)["store"])
        self.assertNotIn("test-key", payload)
        connection.close.assert_called_once()

    def test_missing_key_rejected_without_network(self):
        with self.assertRaises(HTTPException) as failure:
            provider_request(Connection(provider="openai", model="test"), None, [], 512)
        self.assertEqual(failure.exception.status_code, 400)

    @patch("app.api.assistant.HTTPSConnection")
    def test_gemini_uses_native_json_and_keeps_key_in_header(self, connect):
        connection = connect.return_value
        response = connection.getresponse.return_value
        response.status = 200
        response.read.return_value = json.dumps({"candidates": [{
            "content": {"parts": [{"text": "internal", "thought": True}, {"text": '{"action":"reply","answer":'}, {"text": '"Hello"}'}]},
        }]}).encode()
        result = provider_request(Connection(provider="gemini", model="gemini-3.5-flash-lite"), "test-key", [
            {"role": "system", "content": "Return JSON."},
            {"role": "user", "content": "Graph snapshot"},
            {"role": "user", "content": "Earlier question"},
            {"role": "assistant", "content": "Earlier answer"},
            {"role": "user", "content": "New question"},
        ], 512, schema=ConversationPlan)
        self.assertEqual(result, {"action": "reply", "answer": "Hello"})
        connect.assert_called_once_with("generativelanguage.googleapis.com", timeout=40)
        method, path, payload, headers = connection.request.call_args.args
        self.assertEqual((method, path), ("POST", "/v1beta/models/gemini-3.5-flash-lite:generateContent"))
        self.assertEqual(headers["x-goog-api-key"], "test-key")
        self.assertNotIn("test-key", payload + path)
        body = json.loads(payload)
        self.assertEqual(body["systemInstruction"]["parts"], [{"text": "Return JSON."}])
        self.assertEqual([item["role"] for item in body["contents"]], ["user", "model", "user"])
        self.assertEqual(len(body["contents"][0]["parts"]), 2)
        self.assertEqual(body["generationConfig"]["responseMimeType"], "application/json")
        self.assertEqual(body["generationConfig"]["responseJsonSchema"], ConversationPlan.model_json_schema())
        connection.close.assert_called_once()

    @patch("app.api.assistant.HTTPSConnection")
    def test_gemini_invalid_key_does_not_echo_the_provider_error(self, connect):
        response = connect.return_value.getresponse.return_value
        response.status = 400
        response.read.return_value = b'{"error":{"details":[{"reason":"API_KEY_INVALID"}]}}'
        with self.assertRaises(HTTPException) as failure:
            verify_connection(Connection(provider="gemini", model="gemini-3.5-flash-lite"), "test-key")
        self.assertIn("rejected the API key", failure.exception.detail)


if __name__ == "__main__":
    unittest.main()
