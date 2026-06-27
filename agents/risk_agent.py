import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.5-flash")


class RiskAgent:

    def analyze_risk(self, idea):

        prompt = f"""

Analyze this invention:

{idea}

Return ONLY:

Patent Risk: High/Medium/Low
Market Risk: High/Medium/Low
Technical Risk: High/Medium/Low

Do not explain.
Do not add reasons.
One line only.
"""

        response = model.generate_content(prompt)

        return response.text