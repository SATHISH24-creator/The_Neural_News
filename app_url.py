import streamlit as st
import pandas as pd
from datetime import datetime
from utils.prompt import workflow, ArticleData
from content.content_gen_1 import get_content_generator
from utils.gsheet_utils import connect_gspread_client, list_spreadsheets, list_worksheets, save_analyzed_entries_to_sheets
import json
import re
import requests
from urllib.parse import urlparse
import time

# Page configuration
def run_app():
    st.set_page_config(
        page_title="URL News Stream",
        page_icon="📰",
        layout="wide"
    )
    st.title("🤖 URL News Stream")

    # Initialize session state
    if 'analyzed_articles' not in st.session_state:
        st.session_state.analyzed_articles = []
    if 'current_article_index' not in st.session_state:
        st.session_state.current_article_index = 0
    if 'generated_content' not in st.session_state:
        st.session_state.generated_content = {}
    if 'content_type' not in st.session_state:
        st.session_state.content_type = None
    if 'show_content_generation' not in st.session_state:
        st.session_state.show_content_generation = False
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    if 'gsheet_client' not in st.session_state:
        st.session_state.gsheet_client = None
    if 'selected_urls' not in st.session_state:
        st.session_state.selected_urls = []
    if 'url_validation_results' not in st.session_state:
        st.session_state.url_validation_results = {}
    if 'saved_url_presets' not in st.session_state:
        st.session_state.saved_url_presets = {}

    # Initialize content generator
    try:
        content_generator = get_content_generator()
        st.session_state.content_generator_loaded = True
    except Exception as e:
        st.error(f"Failed to load content generator: {str(e)}")
        st.session_state.content_generator_loaded = False
        content_generator = None

    # Initialize Google Sheets client
    try:
        if st.session_state.gsheet_client is None:
            st.session_state.gsheet_client = connect_gspread_client()
            st.session_state.gsheet_connected = True
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {str(e)}")
        st.session_state.gsheet_connected = False

    # Helper function to convert ArticleData to dict format expected by ContentGenerator
    def article_to_dict(article):
        """Convert ArticleData object to dictionary format for ContentGenerator"""
        return {
            'title': article.title,
            'link': article.link,
            'published_date': article.published_date,
            'description': article.description,
            'source': getattr(article, 'source', 'Manual Input'),
            'analyzed': True,
            'analysis_data': {
                'feed_title': article.title,
                'core_message': article.core_message,
                'description': article.description,
                'key_tags': article.key_tags,
                'sector': article.sector
            }
        }

    # Enhanced URL validation functions
    def validate_url(url):
        """Validate if URL is accessible with enhanced checking"""
        try:
            parsed = urlparse(url)
            if not (parsed.netloc and parsed.scheme):
                return False, "Invalid URL format"
            
            # Check if it's a valid HTTP/HTTPS URL
            if parsed.scheme not in ['http', 'https']:
                return False, "URL must use HTTP or HTTPS"
            
            return True, "Valid URL"
        except Exception as e:
            return False, f"URL validation error: {str(e)}"

    def check_url_accessibility(url):
        """Check if URL is accessible (with timeout)"""
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                return True, "Accessible"
            else:
                return False, f"HTTP {response.status_code}"
        except requests.exceptions.Timeout:
            return False, "Timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection Error"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"

    def extract_domain(url):
        """Extract domain from URL for display"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "Unknown"

    def detect_news_source(url):
        """Detect news source from URL"""
        common_sources = {
            'bbc.com': 'BBC',
            'cnn.com': 'CNN',
            'reuters.com': 'Reuters',
            'ap.org': 'Associated Press',
            'nytimes.com': 'New York Times',
            'wsj.com': 'Wall Street Journal',
            'theguardian.com': 'The Guardian',
            'bloomberg.com': 'Bloomberg',
            'techcrunch.com': 'TechCrunch',
            'venturebeat.com': 'VentureBeat',
            'wired.com': 'Wired',
            'engadget.com': 'Engadget'
        }
        
        domain = extract_domain(url)
        for source_domain, source_name in common_sources.items():
            if source_domain in domain:
                return source_name
        return domain

    # Simplified progress callback function - minimal display
    def simple_progress_callback(current, total, message, progress_bar, status_text):
        """Simplified progress callback that shows only essential information"""
        progress_percentage = (current + 1) / total
        progress_bar.progress(progress_percentage)
        
        # Show only high-level progress
        status_text.text(f"📊 Processing... {current + 1} of {total} articles")



    # Enhanced URL Input Section
    st.subheader("📰 Enter News URLs for Analysis")

    # Create tabs for different input methods
    tab1, tab2 = st.tabs(["📝 Manual Input", "⚙️ Advanced Options"])

    with tab1:
        st.markdown("### Manual URL Entry")
        
        # URL input with real-time validation
        col1, col2 = st.columns([2, 1])
        
        with col1:
            url_input = st.text_area(
                "Enter URLs (one per line):",
                height=200,
                placeholder="https://example.com/news-article-1\nhttps://example.com/news-article-2\nhttps://example.com/news-article-3",
                key="manual_input",
                help="Paste your news URLs here. Each URL should be on a separate line."
            )
        
        with col2:
            st.markdown("### URL Statistics")
            
            # Parse URLs from input
            if url_input:
                urls = [url.strip() for url in url_input.split('\n') if url.strip()]
                
                # Quick validation preview
                valid_count = 0
                invalid_count = 0
                domains = set()
                
                for url in urls:
                    is_valid, _ = validate_url(url)
                    if is_valid:
                        valid_count += 1
                        domains.add(extract_domain(url))
                    else:
                        invalid_count += 1
                
                # Display metrics in the specified layout
                metric_col1, metric_col2 = st.columns(2)
                
                with metric_col1:
                    st.metric("Total URLs", len(urls))
                    st.metric("Valid URLs", valid_count)
                
                with metric_col2:
                    st.metric("Invalid URLs", invalid_count)
                    st.metric("Unique Domains", len(domains))
            else:
                st.info("Enter URLs to see statistics")

    with tab2:
        st.markdown("### Advanced Processing Options")
        
        # Processing options
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**URL Filtering:**")
            filter_duplicates = st.checkbox("Remove duplicate URLs", value=True)
            filter_invalid = st.checkbox("Filter out invalid URLs", value=True)
            check_accessibility = st.checkbox("Check URL accessibility", value=False, 
                                            help="This will test if URLs are accessible (slower)")
            
            st.markdown("**Content Filters:**")
            min_content_length = st.slider("Minimum content length", 100, 2000, 500)
            exclude_paywalled = st.checkbox("Exclude paywalled content", value=False)
        
        with col2:
            st.markdown("**Analysis Mode:**")
            processing_mode = st.radio(
                "Choose analysis depth:",
                ["Quick Analysis", "Standard", "Detailed Analysis"],
                help="Quick: Basic extraction, Standard: Full analysis, Detailed: Deep analysis with sentiment"
            )
            
            st.markdown("**Output Options:**")
            include_metadata = st.checkbox("Include metadata extraction", value=True)
            extract_images = st.checkbox("Extract image URLs", value=False)
            generate_summary = st.checkbox("Auto-generate summaries", value=True)

    # Enhanced URL Processing Section
    st.markdown("---")

    # Get URLs for processing
    urls_list = []
    if url_input:
        urls = [url.strip() for url in url_input.split('\n') if url.strip()]
        
        if filter_duplicates:
            urls = list(dict.fromkeys(urls))
        
        if filter_invalid:
            urls_list = [url for url in urls if validate_url(url)[0]]
        else:
            urls_list = urls

    # Enhanced URL Display and Selection
    if urls_list:
        st.markdown(f"### 🔍 URL Analysis Dashboard")
        st.info(f"📋 Found {len(urls_list)} URLs for processing")
        
        # URL validation and selection interface
        with st.expander("📊 URL Validation & Selection", expanded=True):
            
            # Validate URLs button
            validate_col1, validate_col2, validate_col3 = st.columns([2, 1, 1])
            with validate_col1:
                if st.button("🔍 Validate All URLs", key="validate_urls"):
                    with st.spinner("Validating URLs..."):
                        for url in urls_list:
                            is_valid, message = validate_url(url)
                            accessibility_result = "Not checked", "Not checked"
                            
                            if is_valid and check_accessibility:
                                accessibility_result = check_url_accessibility(url)
                            
                            st.session_state.url_validation_results[url] = {
                                'valid': is_valid,
                                'message': message,
                                'accessible': accessibility_result[0],
                                'access_message': accessibility_result[1],
                                'domain': extract_domain(url),
                                'source': detect_news_source(url)
                            }
                    st.success("URL validation complete!")
            
            with validate_col2:
                if st.button("✅ Select All Valid"):
                    valid_urls = [url for url in urls_list 
                                if st.session_state.url_validation_results.get(url, {}).get('valid', True)]
                    st.session_state.selected_urls = valid_urls
                    st.rerun()
            
            with validate_col3:
                if st.button("❌ Clear Selection"):
                    st.session_state.selected_urls = []
                    st.rerun()
            
            # Display URL table with enhanced information
            if st.session_state.url_validation_results:
                url_data = []
                for url in urls_list:
                    result = st.session_state.url_validation_results.get(url, {})
                    url_data.append({
                        'URL': url[:60] + "..." if len(url) > 60 else url,
                        'Source': result.get('source', 'Unknown'),
                        'Status': "✅ Valid" if result.get('valid', True) else "❌ Invalid",
                        'Accessible': result.get('access_message', 'Not checked'),
                        'Domain': result.get('domain', 'Unknown'),
                        'Selected': url in st.session_state.selected_urls
                    })
                
                df = pd.DataFrame(url_data)
                st.dataframe(df, use_container_width=True)
            else:
                # Simple checkbox selection
                st.markdown("**Select URLs to analyze:**")
                if not st.session_state.selected_urls:
                    st.session_state.selected_urls = urls_list.copy()
                
                updated_selected_urls = []
                for i, url in enumerate(urls_list):
                    display_name = f"{detect_news_source(url)} - {url[:50]}..." if len(url) > 50 else url
                    is_selected = url in st.session_state.selected_urls
                    
                    if st.checkbox(display_name, value=is_selected, key=f"url_checkbox_{i}"):
                        updated_selected_urls.append(url)
                
                st.session_state.selected_urls = updated_selected_urls
            
            # Selection summary
            if st.session_state.selected_urls:
                st.success(f"✅ {len(st.session_state.selected_urls)} URLs selected for analysis")
                
                # Show selected URLs summary
                selected_sources = {}
                for url in st.session_state.selected_urls:
                    source = detect_news_source(url)
                    selected_sources[source] = selected_sources.get(source, 0) + 1
                
                st.markdown("**Selected Sources:**")
                source_cols = st.columns(min(len(selected_sources), 4))
                for i, (source, count) in enumerate(selected_sources.items()):
                    with source_cols[i % 4]:
                        st.metric(source, count)
            else:
                st.warning("⚠️ No URLs selected. Please select at least one URL to proceed.")

        # Enhanced Action buttons
        if st.session_state.selected_urls:
            st.markdown("### 🚀 Analysis Actions")
            
            action_col1, action_col2 = st.columns([3, 1])
            
            with action_col1:
                urls_to_analyze = st.session_state.selected_urls
                analyze_button = st.button(
                    f"🚀 Analyze {len(urls_to_analyze)} Selected URLs ({processing_mode})", 
                    type="primary"
                )
            
            with action_col2:
                if st.button("📋 Export URLs"):
                    urls_text = "\n".join(st.session_state.selected_urls)
                    st.download_button(
                        "Download URLs",
                        data=urls_text,
                        file_name=f"selected_urls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )

    # Main analysis logic with minimal progress display
    if 'analyze_button' in locals() and analyze_button and st.session_state.selected_urls:
        urls_to_analyze = st.session_state.selected_urls
        
        # Create minimal progress interface
        st.markdown("### 🔄 Analyzing Articles")
        
        # Create simple progress containers
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        # Simple progress callback wrapper
        def progress_callback(current, total, message):
            simple_progress_callback(current, total, message, progress_bar, status_text)
        
        try:
            st.session_state.analyzed_articles = workflow.process_urls(urls_to_analyze, progress_callback)
            st.session_state.current_article_index = 0
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            if st.session_state.analyzed_articles:
                st.success(f"🎉 Successfully analyzed {len(st.session_state.analyzed_articles)} articles!")
                st.balloons()  # Add celebration animation
            else:
                st.warning("⚠️ No articles were successfully analyzed. Please check the URLs and try again.")
                
        except Exception as e:
            # Clear progress indicators on error
            progress_bar.empty()
            status_text.empty()
            
            st.error(f"❌ Error during analysis: {str(e)}")
            st.info("💡 Please check your URLs and try again. Ensure the articles are accessible and contain readable content.")

    # Show Analyzed Results (Original section - unchanged)
    if st.session_state.analyzed_articles:
        st.header("News Preview")
        
        for idx, entry in enumerate(st.session_state.analyzed_articles):
            # Convert ArticleData to dictionary format for compatibility
            entry_dict = article_to_dict(entry)
            
            with st.expander(entry_dict["analysis_data"].get("feed_title", entry_dict["title"])):
                st.markdown(f"**Original Title:** {entry_dict['title']}")
                st.markdown(f"**Link:** [Read Article]({entry_dict['link']})")
                st.markdown(f"**Published Date:** {entry_dict['published_date']}")
                st.markdown("---")
                st.markdown(f"**Description:** {entry_dict['analysis_data'].get('description', '')}")
                st.markdown(f"**Core Message:** {entry_dict['analysis_data'].get('core_message', '')}")
                st.markdown(f"**Key Tags:** {entry_dict['analysis_data'].get('key_tags', '')}")
                st.markdown(f"**Sector:** {entry_dict['analysis_data'].get('sector', '')}")
                st.markdown("---")

                main_col1, main_col2 = st.columns([1, 1])

                with main_col1:
                    st.markdown("🎯**Content Generation**")

                    linkedin_key = f"linkedin_{idx}"
                    youtube_key = f"youtube_{idx}"
                    newsletter_key = f"newsletter_{idx}"

                    # Content Generation Buttons in Array Format
                    button_cols = st.columns([1, 1, 1, 1])
                    
                    with button_cols[0]:
                        linkedin_generate = st.button("📱LinkedIn", key=f"btn_linkedin_{idx}")
                    with button_cols[1]:
                        youtube_generate = st.button("🎥 YouTube", key=f"btn_youtube_{idx}")
                    with button_cols[2]:
                        newsletter_generate = st.button("📧 Newsletter", key=f"btn_newsletter_{idx}")
                    with button_cols[3]:
                        # Check if any content has been generated
                        has_generated_content = any([
                            linkedin_key in st.session_state.generated_content,
                            youtube_key in st.session_state.generated_content,
                            newsletter_key in st.session_state.generated_content
                        ])
                        
                        if has_generated_content:
                            preview_button = st.button("Preview", key=f"preview_all_{idx}")
                        else:
                            st.write("")  # Empty space when no content generated

                    # Handle Generation Logic
                    if linkedin_generate:
                        with st.spinner("Generating LinkedIn content..."):
                            try:
                                linkedin_content = content_generator.generate_linkedin_content(entry_dict)
                                st.session_state.generated_content[linkedin_key] = linkedin_content
                                st.success("LinkedIn content generated!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error generating LinkedIn content: {str(e)}")

                    if youtube_generate:
                        with st.spinner("Generating YouTube content..."):
                            try:
                                youtube_content = content_generator.generate_youtube_content(entry_dict)
                                st.session_state.generated_content[youtube_key] = youtube_content
                                st.success("YouTube content generated!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error generating YouTube content: {str(e)}")

                    if newsletter_generate:
                        with st.spinner("Generating Newsletter content..."):
                            try:
                                newsletter_content = content_generator.generate_newsletter_content(entry_dict)
                                st.session_state.generated_content[newsletter_key] = newsletter_content
                                st.success("Newsletter content generated!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error generating Newsletter content: {str(e)}")

                    # Handle Preview Logic
                    if has_generated_content and preview_button:
                        st.session_state[f"show_preview_{idx}"] = not st.session_state.get(f"show_preview_{idx}", False)
                        st.rerun()

                    # Display Generated Content Preview
                    if st.session_state.get(f"show_preview_{idx}", False):
                        st.markdown("---")
                        st.markdown("### 📋 Generated Content Preview")
                        
                        # Create tabs for different content types
                        available_tabs = []
                        tab_contents = {}
                        
                        if linkedin_key in st.session_state.generated_content:
                            available_tabs.append("📱LinkedIn")
                            tab_contents["📱LinkedIn"] = st.session_state.generated_content[linkedin_key]
                        
                        if youtube_key in st.session_state.generated_content:
                            available_tabs.append("🎥 YouTube")
                            tab_contents["🎥 YouTube"] = st.session_state.generated_content[youtube_key]
                        
                        if newsletter_key in st.session_state.generated_content:
                            available_tabs.append("📧 Newsletter")
                            tab_contents["📧 Newsletter"] = st.session_state.generated_content[newsletter_key]
                        
                        if available_tabs:
                            tabs = st.tabs(available_tabs)
                            
                            for i, tab_name in enumerate(available_tabs):
                                with tabs[i]:
                                    content = tab_contents[tab_name]
                                    content_type = tab_name  # LinkedIn, YouTube, Newsletter
                                    
                                    st.text_area(f"{tab_name} Content", content, height=200, key=f"{content_type.lower()}_display_{idx}")
                                    
                                    # Download and Close buttons in same row
                                    download_col, close_col = st.columns([2, 1])
                                    with download_col:
                                        st.download_button(
                                            f"Download {content_type} Content", 
                                            data=content, 
                                            file_name=f"{content_type.lower()}_content_{idx}.txt", 
                                            mime="text/plain", 
                                            key=f"download_{content_type.lower()}_{idx}"
                                        )
                                    with close_col:
                                        if st.button("Close Preview", key=f"close_preview_{content_type.lower()}_{idx}"):
                                            st.session_state[f"show_preview_{idx}"] = False
                                            st.rerun()

                # --- Google Sheets Section ---
                with main_col2:
                    st.markdown("📊 **Save to Google Sheets**")
                    try:
                        if st.session_state.gsheet_connected:
                            # Get spreadsheet names
                            sheet_names = list_spreadsheets(st.session_state.gsheet_client)
                            if sheet_names:
                                # Use first spreadsheet as default (Primary Source)
                                default_sheet_name = sheet_names[0]
                                
                                # Open default spreadsheet
                                sheet = st.session_state.gsheet_client.open(default_sheet_name)
                                worksheet_titles = list_worksheets(sheet)
                                
                                # Select worksheet
                                selected_worksheet_title = st.selectbox(
                                    "Select Worksheet", 
                                    worksheet_titles, 
                                    key=f"worksheet_{idx}"
                                )
                                
                                # Get the worksheet
                                worksheet = sheet.worksheet(selected_worksheet_title)
                                
                                # Save button
                                if st.button(f"💾 Save This Entry", key=f"save_{idx}"):
                                    with st.spinner("Saving to Google Sheets..."):
                                        try:
                                            saved_count = save_analyzed_entries_to_sheets(worksheet, [entry_dict])
                                            if saved_count > 0:
                                                st.success(f"✅ Entry saved successfully to '{selected_worksheet_title}'!")
                                            else:
                                                st.warning("⚠️ Entry was not saved (may already exist).")
                                        except Exception as e:
                                            st.error(f"Error saving entry: {str(e)}")
                            else:
                                st.error("No spreadsheets found in your Google account.")
                        else:
                            st.error("❌ Google Sheets not connected")
                            st.write("Check your credentials configuration")
                    except Exception as e:
                        st.error(f"Error accessing Google Sheets: {str(e)}")

    # Reset button
    if st.session_state.analyzed_articles:
        if st.button("🔄 Reset All", type="secondary"):
            st.session_state.analyzed_articles = []
            st.session_state.current_article_index = 0
            st.session_state.generated_content = {}
            st.session_state.content_type = None
            st.session_state.selected_urls = []
            st.rerun()