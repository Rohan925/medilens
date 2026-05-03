import logging
import os

logger = logging.getLogger("llm")


class OpenAIClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.5")
        self._client = None

        if not self.api_key:
            return

        try:
            from langchain_openai import ChatOpenAI

            self._client = ChatOpenAI(
                model=self.model,
                api_key=self.api_key,
                temperature=0,
            )
        except Exception as exc:
            logger.warning("OpenAI client unavailable: %s", exc)
            self._client = None

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


openai_client = OpenAIClient()
