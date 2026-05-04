import asyncio
import unittest
from unittest.mock import patch

from app.api.routes.chat import chat_with_medicine
from app.api.schemas.requests import ChatMessageRequest, ChatRequest


class ChatFlowTests(unittest.TestCase):
    def test_chat_answers_generic_question_without_retrieval(self) -> None:
        request = ChatRequest(
            query="What are common symptoms of dehydration?",
            history=[],
        )

        with patch(
            "app.graph.agents.medicine_resolver_agent.fetch_openfda_data",
            side_effect=AssertionError("retrieval should not run"),
        ), patch(
            "app.graph.agents.medicine_resolver_agent.fetch_pubchem_data",
            side_effect=AssertionError("retrieval should not run"),
        ), patch(
            "app.services.llm.openai_client.openai_client.invoke_text",
            side_effect=[
                "ROUTE: ANSWER\nMEDICINE: NONE",
                "Common symptoms of dehydration include thirst, dry mouth, dark urine, dizziness, and fatigue.",
            ],
        ):
            response = asyncio.run(chat_with_medicine(request))

        self.assertIn("dehydration", response.response.lower())

    def test_chat_retrieves_when_user_asks_about_a_medicine(self) -> None:
        request = ChatRequest(
            query="Tell me about ibuprofen side effects",
            history=[],
        )

        mock_openfda = {
            "drug_name": "Ibuprofen",
            "search_name": "ibuprofen",
            "indications": ["Temporarily relieves minor aches and pains."],
            "warnings": ["May cause stomach bleeding."],
            "dosage": ["Use as directed."],
            "mechanism_of_action": ["Nonsteroidal anti-inflammatory drug."],
            "active_ingredient": ["Ibuprofen"],
            "purpose": ["Pain reliever"],
            "source": "OpenFDA",
            "url": "https://example.test/ibuprofen",
            "product_type": "HUMAN OTC DRUG",
            "is_prescription": False,
            "pharm_class": "NSAID",
            "set_id": "test-set-id",
        }
        mock_pubchem = {
            "drug_name": "Ibuprofen",
            "source": "PubChem",
            "molecular_formula": "C13H18O2",
            "molecular_weight": "206.28",
            "description": "Ibuprofen is a nonsteroidal anti-inflammatory drug.",
            "urls": ["https://example.test/pubchem/ibuprofen"],
        }

        with patch(
            "app.graph.agents.medicine_resolver_agent.fetch_openfda_data",
            side_effect=lambda name: dict(mock_openfda),
        ), patch(
            "app.graph.agents.medicine_resolver_agent.fetch_pubchem_data",
            side_effect=lambda name: dict(mock_pubchem),
        ), patch(
            "app.services.medicine.resolver.fetch_openfda_data",
            side_effect=lambda name: dict(mock_openfda),
        ), patch(
            "app.services.medicine.resolver.fetch_pubchem_data",
            side_effect=lambda name: dict(mock_pubchem),
        ), patch(
            "app.services.llm.openai_client.openai_client.invoke_text",
            side_effect=[
                "ROUTE: RETRIEVE\nMEDICINE: Ibuprofen",
                "CATEGORY: NSAID\nUSES: Pain relief\nWARNINGS: May cause stomach bleeding\nPRESCRIPTION_STATUS: Over-the-Counter (OTC)",
                "Ibuprofen may cause stomach irritation and bleeding risk. Use it carefully.",
            ],
        ):
            response = asyncio.run(chat_with_medicine(request))

        self.assertIn("ibuprofen", response.response.lower())

    def test_chat_can_answer_follow_up_from_history_without_retrieval(self) -> None:
        request = ChatRequest(
            query="What are the side effects?",
            history=[
                ChatMessageRequest(role="user", content="Tell me about ibuprofen"),
                ChatMessageRequest(
                    role="assistant",
                    content="Ibuprofen is an NSAID used for pain relief. Important warnings include stomach bleeding risk.",
                ),
            ],
        )

        with patch(
            "app.graph.agents.medicine_resolver_agent.fetch_openfda_data",
            side_effect=AssertionError("retrieval should not run"),
        ), patch(
            "app.graph.agents.medicine_resolver_agent.fetch_pubchem_data",
            side_effect=AssertionError("retrieval should not run"),
        ), patch(
            "app.services.llm.openai_client.openai_client.invoke_text",
            side_effect=[
                "ROUTE: ANSWER\nMEDICINE: NONE",
                "Based on the earlier ibuprofen context, side effects can include stomach irritation and bleeding risk.",
            ],
        ):
            response = asyncio.run(chat_with_medicine(request))

        self.assertIn("ibuprofen", response.response.lower())
