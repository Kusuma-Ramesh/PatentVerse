from services.gemini_service import generate_innovation


class InnovationAgent:

    def suggest_innovations(self, idea):

        prompt = f"""
Analyze this invention:

{idea}

Return exactly 5 innovation ideas.

Rules:
- One line each.
- Maximum 10 words.
- No numbering.
- No explanations.
- No markdown.
"""

        suggestions = generate_innovation(prompt)

        return suggestions