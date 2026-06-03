import os
import google.generativeai as genai

try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    print(f"Could not configure Gemini API: {e}")


def get_answer_from_gemini(prompt: str) -> str:
    """Gets an answer from the Google Gemini API."""
    # Error handling ensures that if the Gemini API goes downthe main Flask application remains stable.
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Sorry, I couldn't connect to the Gemini service."