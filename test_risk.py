from agents.risk_agent import RiskAgent

agent = RiskAgent()

result = agent.analyze_risk("AI Smart Helmet")

print("Risk Analysis:\n")

for risk, level in result.items():
    print(f"{risk}: {level}")