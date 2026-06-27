from agents.patent_agent import PatentAgent

agent = PatentAgent()

result = agent.search_patents("AI Smart Helmet")

print("Similar Patents Found:\n")

for patent in result:
    print("-", patent)