import streamlit as st
from streamlit_option_menu import option_menu

# Page config
st.set_page_config(page_title="Unified News Toolkit", layout="wide")

# Clean CSS focused on proper navigation
st.markdown("""
    <style>
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Navigation container */
    .css-1y4p8pa.e1fqkh3o3 {
        justify-content: center !important;
        background: #f8f9fa;
        padding: 1rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        border: 1px solid #e9ecef;
    }
    
    /* Navigation links */
    .nav-pills .nav-link {
        padding: 0.75rem 2rem;
        margin: 0 0.5rem;
        border-radius: 8px;
        font-weight: 500;
        color: #495057 !important;
        background: white;
        border: 1px solid #dee2e6;
        transition: all 0.2s ease;
    }
    
    .nav-pills .nav-link:hover {
        background: #e9ecef;
        border-color: #adb5bd;
        color: #212529 !important;
    }
    
    .nav-pills .nav-link.active {
        background: #007bff !important;
        color: white !important;
        border-color: #007bff;
    }
    
    /* Content styling */
    .main-content {
        max-width: 900px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }
    
    .welcome-header {
        text-align: center;
        margin-bottom: 3rem;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        margin: 2rem 0;
    }
    
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        text-align: center;
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #212529;
    }
    
    .feature-description {
        color: #6c757d;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

# Horizontal navigation menu
selected = option_menu(
    menu_title=None,
    options=["🏠 Home", "🔎 RSS News Analyzer", "🔗 URL Content Generator"],
    icons=["", "", ""],
    default_index=0,
    orientation="horizontal",
)

# Home page content
if selected == "🏠 Home":
    # Welcome header
    st.markdown("# 📰 Neural News Arena : News in a Blink")
    
    st.markdown("""
    ---
    
    ## Why Use This Toolkit?

    In today’s fast-paced world, staying updated with the latest news from multiple sources and transforming articles into engaging social media content can be time-consuming. Our toolkit combines powerful automation features to help you:

    - **Aggregate and analyze news** from diverse RSS feeds effortlessly.
    - **Generate concise summaries and insights** that save you valuable reading time.
    - **Transform any news article URL** into ready-to-share social media content with optimized hashtags and formats.
    - **Streamline your workflow** whether you are a journalist, marketer, researcher, or news enthusiast.

    ---
    
    ## Features Overview

    ### RSS News Analyzer
    - Connect to multiple RSS feeds from your favorite news outlets.
    - Extract headlines, summaries, and key information automatically.
    - Monitor news updates in real-time and never miss critical stories.
    - Analyze trends and topics across your selected news sources.

    ### URL Content Generator
    - Input any news article or webpage URL.
    - Automatically generate summaries, key takeaways, and engaging post formats.
    - Create social media-ready content with hashtags tailored to the topic.
    - Perfect for content creators, social media managers, and anyone needing quick article insights.

    ---
    
    ## Getting Started

    Simply select a tool from the navigation menu above. Whether you want to dive into RSS feed analysis or generate content from a specific URL, the toolkit guides you through a smooth and intuitive process.

    Thank you for choosing **Unified News Toolkit** — empowering your news automation journey!

    ---
    
    ### 🚀 How to Get Started
    :information_source: Choose a tool from the navigation menu above to begin analyzing news or generating content.

    ---
    
    ### 💡 Quick Tips
    - **RSS Analyzer**: Perfect for monitoring multiple news sources and getting quick summaries.
    - **URL Generator**: Ideal for creating social media content from specific articles.
    - **Easy Navigation**: Use the horizontal menu to switch between tools seamlessly.
    """)

# RSS News Analyzer
elif selected == "🔎 RSS News Analyzer":
    from app_rss import run_app as run_rss_app
    run_rss_app()

# URL Content Generator
elif selected == "🔗 URL Content Generator":
    from app_url import run_app as run_url_app
    run_url_app()
