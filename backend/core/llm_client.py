from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(self, model="gemini-2.5-flash"):
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model_name = model

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"Error connecting to LLM: {str(e)}"

    async def summarize(self, text: str, mode: str = "standard") -> str:
        prompt = f"""
        Summarize the following medical text. Mode: {mode}
        
        Text:
        {text}
        
        Keep it concise and patient-friendly if requested.
        """
        return self.generate(prompt)

    async def extract_indications(self, raw_text: str) -> str:
        """
        Uses Gemini to extract strictly clinical indications from raw FDA text.
        """
        prompt = f"""
        You are a medical summarization assistant. 
        
        Extract ONLY clinical indications from the provided FDA text.
        
        RULES:
        1. Extract only clinical indications.
        2. Do NOT include headers like "Indications & Usage".
        3. Do NOT include mechanism of action.
        4. Remove repeated phrases like "X tablets are indicated".
        5. Provide MAXIMUM 6 bullet points. No less, no more than exactly what is needed.
        6. Each bullet must be short and clinically precise.
        7. No explanations.
        8. No extra text.
        9. Return ONLY a bulleted list (e.g., "- Headache\\n- Fever").

        TEXT:
        {raw_text}
        """
        
        try:
            # We want deterministic, highly constrained output.
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.1,
                ),
            )
            return response.text.strip()
        except Exception as e:
            return f"Error connecting to LLM: {str(e)}"

    async def generate_answer(self, prompt: str, context: list = None) -> str:
        """
        Async wrapper for generate to satisfy agent interface.
        """
        return self.generate(prompt)

# IMPORTANT: export instance
llm_client = LLMClient()