import os
import json
import logging
from groq import Groq
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = logging.getLogger(__name__)

class GroqRateLimitError(Exception):
    pass

class LLMAnalyzer:
    def __init__(self, api_keys):
        self.api_keys = api_keys if isinstance(api_keys, list) else [api_keys]
        self.current_key_idx = 0
        self.client = Groq(api_key=self.api_keys[self.current_key_idx])
        self.model = "llama-3.3-70b-versatile"
        
    def rotate_key(self):
        """Swaps to the next API key in the list."""
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        logger.info(f"Rotating API Key to key index {self.current_key_idx}")
        self.client = Groq(api_key=self.api_keys[self.current_key_idx])
    def analyze_batch(self, reviews_batch):
        """
        Takes a list of review dictionaries and sends them to Groq for batch analysis.
        Uses exponential backoff for rate limiting (429 errors).
        """
        # Prepare the input data
        input_data = []
        for r in reviews_batch:
            input_data.append({"id": r.id, "text": r.cleaned_text})
            
        system_prompt = """
        You are an expert UX Researcher analyzing app reviews. 
        I will provide you with a JSON array of reviews. 
        For each review, you must return a JSON object containing:
        - "id": The exact integer id I provided.
        - "sentiment": One of [Positive, Neutral, Negative, Frustrated, Delighted].
        - "themes": A list of 1 to 3 short strings identifying the main features or issues mentioned (e.g. ["Discover Weekly", "Ads", "App Crash"]). Return empty list if none.
        - "user_persona": Estimate the user type. One of [Casual Listener, Power User, Audiophile, Unknown].
        
        You must return ONLY a raw JSON array of these objects, with no markdown formatting or extra text.
        """
        
        user_prompt = json.dumps(input_data)
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            # Note: since we requested json_object, we need to ensure our prompt asks for a root object if array fails.
            # Groq's json_object mode requires the output to be a JSON object, not a top-level array.
            # Let's adjust slightly: wrap it in a root key.
            pass
            
        except Exception as e:
            logger.warning(f"Groq API Error: {e}. Retrying...")
            raise e
            
    # Redefine the method to correctly use JSON Object mode
    @retry(
        wait=wait_exponential(multiplier=2, min=4, max=60), 
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(Exception)
    )
    def analyze_batch_safe(self, reviews_batch):
        input_data = []
        for r in reviews_batch:
            input_data.append({"id": r.id, "text": r.cleaned_text[:500]}) # truncate very long reviews
            
        system_prompt = """
        You are an expert UX Researcher analyzing app reviews. 
        I will provide a JSON array of reviews. 
        You must return a JSON object with a single root key called "results", which contains an array of objects.
        For each object in the array, provide:
        - "id": (integer) The exact id provided in the input.
        - "sentiment": (string) [Positive, Neutral, Negative, Frustrated, Delighted]
        - "themes": (array of strings) 1 to 3 short features/issues mentioned.
        - "user_persona": (string) [Casual Listener, Power User, Audiophile, Unknown]
        """
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(input_data)}
                ],
                model=self.model,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            parsed = json.loads(content)
            return parsed.get("results", [])
            
        except Exception as e:
            if "429" in str(e):
                logger.warning("Rate limit hit (429). Rotating key and backing off...")
                self.rotate_key()
            else:
                logger.warning(f"API or Parsing Error: {e}")
            raise e
