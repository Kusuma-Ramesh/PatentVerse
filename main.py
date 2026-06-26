from agents.patent_agent import PatentAgent
from agents.product_agent import ProductAgent
from agents.innovation_agent import InnovationAgent
from agents.risk_agent import RiskAgent


def main():
    idea = input("Enter your product idea: ")

    patent_agent = PatentAgent()
    product_agent = ProductAgent()
    innovation_agent = InnovationAgent()
    risk_agent = RiskAgent()

    print("\n--- PatentVerse Analysis ---\n")

    print(patent_agent.search_patents(idea))
    print(product_agent.search_products(idea))
    print(innovation_agent.suggest_innovations(idea))
    print(risk_agent.analyze_risk(idea))


if __name__ == "__main__":
    main()
