import os
import logging

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()
logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        self._llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            google_api_key=api_key,
        )

    async def generate_answer(self, prompt: str) -> str:
        try:
            response = await self._llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as exc:
            logger.warning("LLM generate failed, using fallback response: %s", exc)
            return self._fallback_response(prompt)

    def summarize(self, text: str) -> str:
        try:
            response = self._llm.invoke(
                [HumanMessage(content=f"Summarize this medical text clearly and briefly:\n\n{text}")]
            )
            return response.content
        except Exception as exc:
            logger.warning("LLM summarize failed, using fallback summary: %s", exc)
            cleaned = " ".join(text.split())
            if not cleaned:
                return ""
            if len(cleaned) <= 300:
                return cleaned
            return cleaned[:297] + "..."

    def _fallback_response(self, prompt: str) -> str:
        prompt_lower = prompt.lower()

        if "respond with:" in prompt_lower and "valid / partial / invalid" in prompt_lower:
            return "PARTIAL"

        if "return only the name" in prompt_lower and "medicine name" in prompt_lower:
            return "Unknown"

        if "consult a healthcare professional for proper medical advice" in prompt_lower:
            return (
                "I couldn't verify the full answer from the language model right now. "
                "Based on the available medical context, please refer to the listed uses and warnings. "
                "Consult a healthcare professional for proper medical advice."
            )

        return (
            "I couldn't complete the language model request right now. "
            "Please try again later."
        )


llm_client = LLMClient()


async def generate_answer(prompt: str) -> str:
    return await llm_client.generate_answer(prompt)
