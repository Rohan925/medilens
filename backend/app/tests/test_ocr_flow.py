import asyncio
import io
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

from app.api.routes.ocr import ocr_image
from app.domain.enums import RequestMode
from app.graph.runners.ocr_graph import run_ocr_graph
from app.graph.state import GraphState


class OcrFlowTests(unittest.TestCase):
    def test_ocr_route_rejects_non_image_uploads(self) -> None:
        upload = UploadFile(
            file=io.BytesIO(b"not-an-image"),
            filename="notes.txt",
            headers=Headers({"content-type": "text/plain"}),
        )

        with self.assertRaises(HTTPException) as exc_info:
            asyncio.run(ocr_image(upload))

        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertIn("Unsupported file type", exc_info.exception.detail)

    def test_ocr_route_rejects_oversized_uploads(self) -> None:
        upload = UploadFile(
            file=io.BytesIO(b"x" * ((5 * 1024 * 1024) + 1)),
            filename="label.jpg",
            headers=Headers({"content-type": "image/jpeg"}),
        )

        with self.assertRaises(HTTPException) as exc_info:
            asyncio.run(ocr_image(upload))

        self.assertEqual(exc_info.exception.status_code, 413)
        self.assertIn("too large", exc_info.exception.detail)

    def test_ocr_graph_reuses_search_flow_after_image_extraction(self) -> None:
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
        state = GraphState(
            mode=RequestMode.OCR,
            image_path="/tmp/fake-image.jpg",
        )

        with patch(
            "app.graph.agents.ocr_agent.extract_medicine_from_image",
            return_value=type(
                "Result",
                (),
                {
                    "medicine_name": "Ibuprofen",
                    "raw_text": "IBUPROFEN TABLETS",
                    "confidence": 92.0,
                    "error": None,
                },
            )(),
        ), patch(
            "app.graph.agents.medicine_resolver_agent.fetch_openfda_data",
            side_effect=lambda name: dict(mock_openfda),
        ), patch(
            "app.graph.agents.medicine_resolver_agent.fetch_pubchem_data",
            side_effect=lambda name: dict(mock_pubchem),
        ):
            final_state = run_ocr_graph(state)

        response = final_state.response
        self.assertEqual(response["medicine"], "Ibuprofen")
        self.assertTrue(response["success"])
        self.assertEqual(response["confidence"], 92.0)
        self.assertIsNotNone(response["summary"])
        self.assertEqual(response["summary"]["category"], "NSAID")
        self.assertEqual(len(response["citations"]), 2)
