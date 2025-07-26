import streamlit as st

st.set_page_config(page_title="Unified News Toolkit", layout="wide")
st.sidebar.title("🧭 Navigation")
app_choice = st.sidebar.radio("Choose App", ["🔎 RSS News Analyzer", "🔗 URL Content Generator"])

if app_choice == "🔎 RSS News Analyzer":
    from app_rss import run_app as run_rss_app
    run_rss_app()

elif app_choice == "🔗 URL Content Generator":
    from app_url import run_app as run_url_app
    run_url_app()
