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

    patents = patent_agent.search_patents(idea)
    products = product_agent.search_products(idea)
    innovations = innovation_agent.suggest_innovations(idea)
    risks = risk_agent.analyze_risk(idea)

    print("\n========== PatentVerse Report ==========\n")

    print("📜 Related Patents:")
    for patent in patents:
        print("-", patent)

    print("\n🛒 Similar Products:")
    for product in products:
        print("-", product)

    print("\n💡 Innovation Suggestions:")
    for innovation in innovations:
        print("-", innovation)

    print("\n⚠️ Risk Analysis:")
    for key, value in risks.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
