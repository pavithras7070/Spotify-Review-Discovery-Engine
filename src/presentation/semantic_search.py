import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

@st.cache_resource
def load_model():
    """Loads the embedding model only once to save time."""
    return SentenceTransformer('all-MiniLM-L6-v2')

class SemanticSearcher:
    def __init__(self, reviews_df):
        self.df = reviews_df.copy()
        # Drop rows where cleaned_text is empty or not string
        self.df = self.df[self.df['cleaned_text'].astype(bool)]
        self.df = self.df.reset_index(drop=True)
        
        self.model = load_model()
        self.embeddings = self._generate_embeddings()
        
    @st.cache_data(show_spinner=False)
    def _generate_embeddings(_self):
        """Generates embeddings for all reviews and caches them in Streamlit."""
        texts = _self.df['cleaned_text'].tolist()
        # Progress indicator will be handled in app.py
        embeddings = _self.model.encode(texts, show_progress_bar=False)
        return embeddings

    def search(self, query, top_k=50):
        """Embeds the query and returns all highly similar reviews."""
        query_embedding = self.model.encode([query])
        
        # Calculate cosine similarity between query and all reviews
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top K indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = similarities[idx]
            # Lower the threshold slightly to catch more context, but keep it relevant
            if score > 0.12: 
                row = self.df.iloc[idx]
                results.append({
                    "score": round(float(score) * 100, 1),
                    "text": row['cleaned_text'],
                    "sentiment": row['sentiment'],
                    "date": row['date'],
                    "source": row['source']
                })
        return results

    def answer_question(self, query, results, api_keys):
        """Uses Groq to synthesize an answer to the query based purely on the retrieved reviews."""
        if not results:
            return "No relevant reviews found to answer this question."
            
        from groq import Groq
        import time
        
        # Prepare API Keys
        if isinstance(api_keys, str):
            api_keys = [api_keys]
            
        # Bundle the context (cap at 40 reviews to protect the 12K TPM free tier limit)
        context = ""
        for r in results[:40]:
            context += f"- User Feedback ({r['sentiment']}): {r['text']}\n"
            
        system_prompt = (
            "You are an expert product analyst answering user questions based ONLY on the provided user reviews. "
            "Do not invent or hallucinate information. If the reviews do not contain the answer, say 'I cannot answer this based on the provided reviews.' "
            "Be direct, concise, and professional. When discussing multiple user segments, present each segment clearly one after the other. You MAY use bullet points or new lines for readability. "
            "CRITICAL RULES: \n"
            "1. If the question specifically asks about 'user segments', 'groups', or 'types of users', explicitly name and group them using highly specific, music-discovery-focused segment names (e.g., 'Algorithm-fatigued listeners', 'Active playlist curators'). Do not use generic terms.\n"
            "2. If the question does NOT ask about user segments, just answer the question directly without forcing segment names.\n"
            "3. If the question asks about 'challenges', 'issues', or 'problems', you MUST ignore 'Delighted' or happy users in your answer, as they do not face these challenges."
        )
        
        user_prompt = f"Context Reviews:\n{context}\n\nQuestion: {query}"
        
        # Try keys until one works
        for key in api_keys:
            try:
                client = Groq(api_key=key)
                response = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.2,
                )
                return response.choices[0].message.content
            except Exception as e:
                if "429" in str(e):
                    continue # Try the next key
                else:
                    return f"API Error: {str(e)}"
                    
        return "All API keys are currently rate-limited. Please try again later."
