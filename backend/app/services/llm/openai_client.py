import logging
import mimetypes
import os
from base64 import b64encode

logger = logging.getLogger("llm")


class OpenAIClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.5")
        self.vision_model = os.getenv("OPENAI_VISION_MODEL", self.model)
        self._client = None
        self._raw_client = None

        if not self.api_key:
            return

        try:
            from langchain_openai import ChatOpenAI
            from openai import OpenAI

            self._client = ChatOpenAI(
                model=self.model,
                api_key=self.api_key,
                temperature=0,
            )
            self._raw_client = OpenAI(api_key=self.api_key)
        except Exception as exc:
            logger.warning("OpenAI client unavailable: %s", exc)
            self._client = None
            self._raw_client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def invoke_text(self, prompt: str) -> str | None:
        if not self._client or not prompt.strip():
            return None
        try:
            logger.info("LLM invoke start: model=%s", self.model)
            response = self._client.invoke(prompt)
            output_text = (response.content or "").strip()
            if not output_text:
                logger.warning("LLM invoke returned empty content")
                return None
            logger.info("LLM invoke success: output=%r", output_text[:200])
            return output_text
        except Exception as exc:
            logger.warning("OpenAI invocation failed: %s", exc)
            return None

    def invoke_image_text(self, image_path: str, prompt: str) -> str | None:
        if not self._raw_client or not image_path or not prompt.strip():
            return None

        try:
            with open(image_path, "rb") as image_file:
                mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"
                encoded_image = b64encode(image_file.read()).decode("utf-8")

            logger.info("LLM image invoke start: model=%s", self.vision_model)
            response = self._raw_client.responses.create(
                model=self.vision_model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {
                                "type": "input_image",
                                "image_url": f"data:{mime_type};base64,{encoded_image}",
                            },
                        ],
                    }
                ],
            )

            output_text = (getattr(response, "output_text", "") or "").strip()
            if not output_text:
                logger.warning("LLM image invoke returned empty content")
                return None
            logger.info("LLM image invoke success: output=%r", output_text[:200])
            return output_text
        except Exception as exc:
            logger.warning("OpenAI image invocation failed: %s", exc)
            return None


openai_client = OpenAIClient()
