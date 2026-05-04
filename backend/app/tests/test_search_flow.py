import asyncio
import unittest
from unittest.mock import patch
from unittest.mock import PropertyMock

import requests
from pydantic import ValidationError

from app.api.routes.search import search_medicine
from app.api.schemas.requests import SearchRequest
from app.services.medicine import resolver
from app.services.retrieval.openfda_client import fetch_openfda_data


MOCK_OPENFDA = {
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
    "pharm_class": "Nonsteroidal Anti-inflammatory Drug",
    "set_id": "test-set-id",
}

MOCK_PUBCHEM = {
    "drug_name": "Ibuprofen",
    "source": "PubChem",
    "molecular_formula": "C13H18O2",
    "molecular_weight": "206.28",
    "description": "Ibuprofen is a nonsteroidal anti-inflammatory drug.",
    "urls": ["https://example.test/pubchem/ibuprofen"],
}

MOCK_SUMMARY = (
    "CATEGORY: NSAID\n"
    "USES: Pain relief | Fever reduction\n"
    "WARNINGS: May cause stomach bleeding\n"
    "PRESCRIPTION_STATUS: Over-the-Counter (OTC)"
)


class SearchFlowTests(unittest.TestCase):
    def test_search_request_rejects_whitespace_only_query(self) -> None:
        with self.assertRaises(ValidationError):
            SearchRequest(query="   ")

    def test_openfda_falls_through_from_brand_to_generic_lookup(self) -> None:
        class MockResponse:
            def __init__(self, status_code: int, payload: dict) -> None:
                self.status_code = status_code
                self._payload = payload

            def raise_for_status(self) -> None:
                if self.status_code >= 400:
                    response = requests.Response()
                    response.status_code = self.status_code
                    raise requests.HTTPError(response=response)

            def json(self) -> dict:
                return self._payload

        result_payload = {
            "results": [
                {
                    "openfda": {
                        "product_type": ["HUMAN OTC DRUG"],
                        "pharm_class_epc": ["Nonsteroidal Anti-inflammatory Drug [EPC]"],
                        "spl_set_id": ["generic-hit"],
                    },
                    "indications_and_usage": ["Temporarily relieves minor aches and pains."],
                    "warnings": ["May cause stomach bleeding."],
                }
            ]
        }

        responses = [
            MockResponse(404, {}),
            MockResponse(200, result_payload),
        ]

        with patch(
            "app.services.retrieval.openfda_client.requests.get",
            side_effect=responses,
        ) as mock_get:
            result = fetch_openfda_data("ibuprofen")

        self.assertIsNotNone(result)
        self.assertEqual(result["search_name"], "ibuprofen")
        self.assertEqual(result["set_id"], "generic-hit")
        self.assertEqual(result["pharm_class"], "Nonsteroidal Anti-inflammatory Drug")
        self.assertEqual(mock_get.call_count, 2)
        self.assertIn("brand_name.exact", mock_get.call_args_list[0].kwargs["params"]["search"])
        self.assertIn("generic_name.exact", mock_get.call_args_list[1].kwargs["params"]["search"])

    def test_resolver_prefers_single_text_input_for_search(self) -> None:
        with patch.object(
            type(resolver.openai_client),
            "available",
            new_callable=PropertyMock,
            return_value=True,
        ), patch(
            "app.services.medicine.resolver.openai_client.invoke_text",
            return_value="Ibuprofen",
        ) as mock_invoke:
            result = resolver.resolve_medicine_name(input_text="ibuprofen")

        self.assertEqual(result.normalized_name, "Ibuprofen")
        self.assertEqual(mock_invoke.call_count, 1)
        prompt = mock_invoke.call_args.args[0]
        self.assertIn("\nibuprofen\n", prompt)
        self.assertNotIn("\nibuprofen\nibuprofen\n", prompt)

    def test_search_route_returns_expected_summary_shape(self) -> None:
        with patch(
            "app.graph.agents.medicine_resolver_agent.fetch_openfda_data",
            side_effect=lambda name: dict(MOCK_OPENFDA),
        ), patch(
            "app.graph.agents.medicine_resolver_agent.fetch_pubchem_data",
            side_effect=lambda name: dict(MOCK_PUBCHEM),
        ), patch(
            "app.services.llm.openai_client.openai_client.invoke_text",
            return_value="Ibuprofen",
        ):
            response = asyncio.run(search_medicine(SearchRequest(query="ibuprofen")))

        self.assertEqual(response.name, "Ibuprofen")
        self.assertEqual(response.category, "Nonsteroidal Anti-inflammatory Drug")
        self.assertEqual(response.uses, ["Temporarily relieves minor aches and pains"])
        self.assertEqual(response.warnings, ["May cause stomach bleeding"])
        self.assertEqual(response.prescription_status, "Over-the-Counter (OTC)")
        self.assertEqual(response.mechanism, ["Nonsteroidal anti-inflammatory drug."])
        self.assertEqual(len(response.citations), 2)
        self.assertEqual(response.citations[0].source, "FDA DailyMed")
        self.assertEqual(response.citations[1].source, "PubChem")
