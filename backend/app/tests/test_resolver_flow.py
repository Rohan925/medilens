import unittest
from unittest.mock import patch
from unittest.mock import PropertyMock

from app.services.medicine import resolver
from app.services.medicine.resolver import resolve_medicine_name


class ResolverFlowTests(unittest.TestCase):
    def test_resolver_uses_llm_to_extract_and_normalize_medicine_name(self) -> None:
        with patch.object(
            type(resolver.openai_client),
            "available",
            new_callable=PropertyMock,
            return_value=True,
        ), patch(
            "app.services.medicine.resolver.openai_client.invoke_text",
            return_value="Adderall",
        ):
            result = resolve_medicine_name(
                input_text="Hi tell me about adderall",
            )

        self.assertEqual(result.normalized_name, "Adderall")

    def test_resolver_uses_medicine_name_as_primary_normalization_input(self) -> None:
        with patch.object(
            type(resolver.openai_client),
            "available",
            new_callable=PropertyMock,
            return_value=True,
        ), patch(
            "app.services.medicine.resolver.openai_client.invoke_text",
            return_value="Amphetamine Dextroamphetamine",
        ) as mock_invoke:
            result = resolve_medicine_name(
                medicine_name="Adderall XR",
                input_text="tell me about adderall xr",
            )

        self.assertEqual(result.normalized_name, "Amphetamine Dextroamphetamine")
        prompt = mock_invoke.call_args.args[0]
        self.assertIn("\nAdderall XR\n", prompt)
