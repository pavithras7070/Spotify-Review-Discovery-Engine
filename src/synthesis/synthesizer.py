import json
import logging
from groq import Groq
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = logging.getLogger(__name__)

class InsightSynthesizer:
    def __init__(self, api_keys):
        self.api_keys = api_keys if isinstance(api_keys, list) else [api_keys]
        self.current_key_idx = 0
        self.client = Groq(api_key=self.api_keys[self.current_key_idx])
        self.model = "llama-3.3-70b-versatile"
        
    def rotate_key(self):
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        logger.info(f"Rotating API Key to key index {self.current_key_idx}")
        self.client = Groq(api_key=self.api_keys[self.current_key_idx])
        
    @retry(
        wait=wait_exponential(multiplier=2, min=4, max=60), 
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(Exception)
    )
    def generate_insight(self, theme_name, reviews):
        """
        Takes a theme and a list of up to 30 sample reviews and generates 
        an executive summary using the LLM.
        """
        # Take a max of 30 reviews to avoid context window explosion
        sample_reviews = reviews[:30]
        
        input_data = []
        for r in sample_reviews:
            input_data.append({"sentiment": r["sentiment"], "text": r["text"]})
            
        system_prompt = f"""
        You are an expert Product Manager analyzing user feedback for the theme: "{theme_name}".
        I will provide a JSON array of up to 30 sample user reviews that have been tagged with this theme.
        
        Your task:
        Write a concise, 2-3 sentence executive summary explaining exactly what the users are saying about this theme.
        Focus on specific actionable insights (e.g. "Users are frustrated because X happens when they try to Y").
        Do not use filler words. Be direct and objective.
        
        You must return a raw JSON object with exactly one key: "insight_summary", containing your string response.
        """
        
        user_prompt = json.dumps(input_data)
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            parsed = json.loads(content)
            return parsed.get("insight_summary", "Failed to generate summary.")
            
        except Exception as e:
            if "429" in str(e):
                logger.warning(f"Rate limit hit while synthesizing '{theme_name}'. Rotating key and backing off...")
                self.rotate_key()
            else:
                logger.error(f"API Error synthesizing '{theme_name}': {e}")
            raise e
