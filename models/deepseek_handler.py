from together import Together
import os


def get_answer_from_deepseek(prompt: str) -> str:
    """Gets an answer from the DeepSeek model via the Together.ai API."""
    # Error handling ensures that if the DeepSeek API goes downthe main Flask application remains stable.
    try:
        client = Together()
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3", 
            messages=[{"role": "user", "content": prompt}],
            stream=False 
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling Together.ai API for DeepSeek: {e}")
        return "Sorry, I couldn't connect to the DeepSeek service via Together.ai."