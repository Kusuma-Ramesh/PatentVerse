import streamlit as st

from agents.patent_agent import PatentAgent
from agents.product_agent import ProductAgent
from agents.innovation_agent import InnovationAgent
from agents.risk_agent import RiskAgent

st.set_page_config(
    page_title="PatentVerse",
    page_icon="🚀"
)

st.title("🚀 PatentVerse")
st.subheader("Multi-Agent Innovation and Patent Intelligence System")

idea = st.text_input(
    "Enter your product idea:",
    placeholder="Example: AI Smart Helmet"
)

if st.button("Analyze Idea"):

    patent_agent = PatentAgent()
    product_agent = ProductAgent()
    innovation_agent = InnovationAgent()
    risk_agent = RiskAgent()

    patents = patent_agent.search_patents(idea)
    products = product_agent.search_products(idea)
    innovations = innovation_agent.suggest_innovations(idea)
    risks = risk_agent.analyze_risk(idea)

    st.header("📜 Related Patents")

    for patent in patents:
        st.write("•", patent)

    st.header("🛒 Similar Products")

    for product in products:
        st.write("•", product)

    st.header("💡 Innovation Suggestions")

    for innovation in innovations:
        st.write("•", innovation)

    st.header("⚠️ Risk Analysis")

    for key, value in risks.items():
        st.write(f"{key}: {value}")
