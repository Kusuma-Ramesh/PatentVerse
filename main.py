from agents.patent_agent import PatentAgent
from agents.risk_agent import RiskAgent
from services.gemini_service import generate_innovation


idea = input("Enter your invention idea: ")

print("\nSearching similar patents...\n")
patent_agent = PatentAgent()
patents = patent_agent.search_patents(idea)

for patent in patents:
    print("-", patent)


print("\nInnovation Suggestions:\n")
innovations = generate_innovation(idea)
print(innovations)


print("\nRisk Analysis:\n")
risk_agent = RiskAgent()
risks = risk_agent.analyze_risk(idea)

for risk, level in risks.items():
    print(f"{risk}: {level}")