import asyncio
import unittest
from unittest.mock import patch

from app.api.routes.search import search_medicine
from app.api.schemas.requests import SearchRequest


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
    def test_search_route_returns_expected_summary_shape(self) -> None:
        with patch(
            "app.graph.agents.medicine_resolver_agent.fetch_openfda_data",
            side_effect=lambda name: dict(MOCK_OPENFDA),
        ), patch(
            "app.graph.agents.medicine_resolver_agent.fetch_pubchem_data",
            side_effect=lambda name: dict(MOCK_PUBCHEM),
        ), patch(
            "app.services.medicine.resolver.fetch_openfda_data",
            side_effect=lambda name: dict(MOCK_OPENFDA),
        ), patch(
            "app.services.medicine.resolver.fetch_pubchem_data",
            side_effect=lambda name: dict(MOCK_PUBCHEM),
        ), patch(
            "app.services.llm.openai_client.openai_client.invoke_text",
            return_value=MOCK_SUMMARY,
        ):
            response = asyncio.run(search_medicine(SearchRequest(query="ibuprofen")))

        self.assertEqual(response.name, "Ibuprofen")
        self.assertEqual(response.category, "NSAID")
        self.assertEqual(response.uses, ["Pain relief", "Fever reduction"])
        self.assertEqual(response.warnings, ["May cause stomach bleeding"])
        self.assertEqual(response.prescription_status, "Over-the-Counter (OTC)")
        self.assertEqual(response.mechanism, ["Nonsteroidal anti-inflammatory drug."])
        self.assertEqual(len(response.citations), 2)
        self.assertEqual(response.citations[0].source, "FDA DailyMed")
        self.assertEqual(response.citations[1].source, "PubChem")
