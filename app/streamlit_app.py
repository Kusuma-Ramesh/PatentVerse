import streamlit as st

st.set_page_config(
    page_title="PatentVerse",
    page_icon="🚀",
)

st.title("🚀 PatentVerse")
st.subheader("Multi-Agent Innovation and Patent Intelligence System")

idea = st.text_input(
    "Enter your product idea:",
    placeholder="Example: AI Smart Helmet"
)

if st.button("Analyze Idea"):
    st.success("Patent Search Agent is analyzing...")
    st.success("Product Search Agent is analyzing...")
    st.success("Innovation Agent is analyzing...")
    st.success("Risk Agent is analyzing...")
