import os
import openai

def get_answer_from_gpt4(prompt: str) -> str:
    """Gets an answer from the GPT-4 API."""
    # Error handling ensures that if the GPT-4 API goes downthe main Flask application remains stable.
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling GPT-4 API: {e}")
        return "Sorry, I couldn't connect to the GPT-4 service."