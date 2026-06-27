import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.5-flash")


def generate_innovation(idea):

    prompt = f"""
Analyze this invention:

{idea}

Return exactly 5 innovation ideas.

Rules:
- One line only for each idea.
- Maximum 8 words.
- No numbers.
- No bullets.
- No markdown.
- No headings.
- No explanations.

Example:

Add emergency alerts
Enable mobile monitoring
Use predictive analytics
Improve battery life
Provide cloud connectivity
"""

    response = model.generate_content(prompt)

    return response.text