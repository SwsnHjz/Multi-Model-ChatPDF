import os
import openai

def get_answer_from_mistral(prompt: str) -> str:
    """Gets an answer from the Mistral API."""
    # Error handling ensures that if the Mistral API goes downthe main Flask application remains stable.
    try:
        client = openai.OpenAI(
            api_key=os.getenv("MISTRAL_API_KEY"),
            base_url="https://api.mistral.ai/v1/"
        )
        response = client.chat.completions.create(
            model="mistral-small-latest", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling Mistral API: {e}")
        return "Sorry, the Mistral service is temporarily unavailable or the document context is too large. Please try again or use a different model."