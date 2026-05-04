import unittest
from unittest.mock import patch

from app.domain.enums import RequestMode
from app.graph.agents.summarizer_agent import summarizer_agent
from app.graph.state import GraphState


class SummarizerFlowTests(unittest.TestCase):
    def test_summarizer_skips_enrichment_when_core_summary_is_present(self) -> None:
        state = GraphState(
            mode=RequestMode.SEARCH,
            resolved_medicine="Ibuprofen",
            openfda_data={
                "indications": ["Temporarily relieves minor aches and pains."],
                "warnings": ["May cause stomach bleeding."],
                "mechanism_of_action": ["Nonsteroidal anti-inflammatory drug."],
                "product_type": "HUMAN OTC DRUG",
                "is_prescription": False,
                "pharm_class": "Nonsteroidal Anti-inflammatory Drug",
            },
            pubchem_data={},
        )

        with patch(
            "app.graph.agents.summarizer_agent.openai_client.invoke_text",
            side_effect=AssertionError("enrichment should not run"),
        ):
            result = summarizer_agent(state)

        self.assertIsNotNone(result.structured_summary)
        self.assertEqual(result.structured_summary.category, "Nonsteroidal Anti-inflammatory Drug")
        self.assertEqual(result.structured_summary.uses, [])
        self.assertEqual(
            result.structured_summary.warnings,
            ["May cause stomach bleeding"],
        )
