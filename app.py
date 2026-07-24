import streamlit as st
import json
import pandas as pd
from scraper_raw import scrape_multiple_pages
from urllib.parse import urlparse

# --- UTeM Portal Directory ---
UTEM_URLS = {
    "FAIX - Faculty of Artificial Intelligence": "https://faix.utem.edu.my/",
    "UTeM Main Website": "https://www.utem.edu.my/en/",
    "FTKE - Faculty of Electrical Engineering Technology": "https://ftke.utem.edu.my/en/",
    "FTKEK - Faculty of Electronic & Computer Engineering": "https://ftkek.utem.edu.my/",
    "FTKIP - Faculty of Manufacturing Engineering": "https://ftkip.utem.edu.my/",
    "FTKM - Faculty of Mechanical Engineering Technology": "https://ftkm.utem.edu.my/",
    "FTMK - Faculty of Information & Communication Tech": "https://ftmk.utem.edu.my/web/",
    "FPTT - Faculty of Technology Management & Technopreneurship": "https://fptt.utem.edu.my/",
    "Library": "https://library.utem.edu.my/en/",
    "Exam Portal": "https://examportal.utem.edu.my/",
    "SPS - Institute of Graduate Studies": "https://sps.utem.edu.my/",
    "Registrar (Pendaftar)": "https://pendaftar.utem.edu.my/en/",
    "Bursary (Bendahari)": "https://bendahari.utem.edu.my/ms/",
    "Chancellery (Canselori)": "https://canselori.utem.edu.my/en/",
    "Health Center (Pusat Kesihatan)": "https://pusatkesihatan.utem.edu.my/en/",
    "Sports Center (Pusat Sukan)": "https://pusatsukan.utem.edu.my/en/",
    "Security (Keselamatan)": "https://keselamatan.utem.edu.my/en/",
    "Sustainability": "https://sustainability.utem.edu.my/ms/",
    "UTeM Access": "https://utemaccess.utem.edu.my/ms/",
    "CRIM": "https://crim.utem.edu.my/",
    "Publisher (Penerbit)": "https://penerbit.utem.edu.my/",
    "CODL": "https://codl.utem.edu.my/",
    "CISMO": "https://cismo.utem.edu.my/",
    "SMTC": "https://smtc.utem.edu.my/",
    "RICE": "https://rice.utem.edu.my/en/",
    "CELL": "https://cell.utem.edu.my/en/",
    "CDO": "https://cdo.utem.edu.my/ms/",
    "CAES": "https://caes.utem.edu.my/en/",
    "TF": "https://tf.utem.edu.my/",
    "PPF": "https://ppf.utem.edu.my/ms/",
    "IPTK": "https://iptk.utem.edu.my/en/",
    "PPSKR": "https://ppskr.utem.edu.my/en/"
}

# 1. Page Configuration
st.set_page_config(
    page_title="Web Crawler",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Setup App Memory (Session State)
if "scraped_data" not in st.session_state:
    st.session_state.scraped_data = None
if "final_filename" not in st.session_state:
    st.session_state.final_filename = "data.json"
if "target_urls" not in st.session_state:
    st.session_state.target_urls = []

# 3. Custom CSS
st.markdown("""
    <style>
    .stDownloadButton>button {
        width: 100%;
        font-weight: bold;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)


def crawler_page():
    # 4. Main Layout
    left_panel, right_panel = st.columns([1, 2], gap="large")

    with left_panel:
        st.title("🕷️ Web Crawler")
        st.write("") 
        
        st.markdown("### 1. Add Target URLs")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            # Modified to show URL directly
            url_choices = list(UTEM_URLS.values()) + ["Custom URL..."]
            selected_url = st.selectbox("🎯 Select Target UTeM Portal URL:", url_choices)
            if selected_url == "Custom URL...":
                url_input = st.text_input("🌐 Enter Custom URL:", "https://")
            else:
                url_input = selected_url
                
        with col2:
            st.write("")
            st.write("")
            if st.button("➕ Add URL", use_container_width=True):
                if url_input and url_input not in st.session_state.target_urls:
                    st.session_state.target_urls.append(url_input)
                    st.rerun()
                    
        st.markdown("**Current Crawl Queue:**")
        if st.session_state.target_urls:
            for i, url in enumerate(st.session_state.target_urls):
                c1, c2 = st.columns([8, 1])
                c1.code(url)
                if c2.button("❌", key=f"del_{i}"):
                    st.session_state.target_urls.pop(i)
                    st.rerun()
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.target_urls = []
                st.rerun()
        else:
            st.info("Queue is empty. Add URLs to begin.")
            
        st.markdown("### 2. Configure & Start")
            
        max_pages_input = st.number_input("📄 Max Pages per site:", min_value=1, value=200)
        
        with st.expander("🛠️ Advanced Options", expanded=False):
            ignore_input = st.text_input("🚫 Ignore URLs containing:", "contact, login, register, admin")
        
        start_crawling = st.button("🚀 Start Crawling Queue", type="primary", use_container_width=True)

    with right_panel:
        # Trigger the crawling process
        if start_crawling:
            if not st.session_state.target_urls:
                st.warning("Please add at least one URL to the queue first.")
            else:
                st.session_state.scraped_data = None 
                
                ignore_list = [word.strip() for word in ignore_input.split(',')]
                
                with st.status("🤖 Crawling multiple sites in parallel...", expanded=True) as status:
                    st.write(f"Starting parallel crawl for {len(st.session_state.target_urls)} websites...")
                    
                    # Call scrape_multiple_pages which now returns a dictionary per URL
                    results = scrape_multiple_pages(st.session_state.target_urls, max_pages_input, ignore_list)
                    
                    if "crawler_error" in results:
                        st.error(f"Fatal Session Error: {results['crawler_error']['error']}")
                        status.update(label="Crawling Failed", state="error", expanded=True)
                    else:
                        status.update(label="Crawling Complete!", state="complete", expanded=False)
                        st.session_state.scraped_data = results

        # Display the results separately using tabs
        if st.session_state.scraped_data and "crawler_error" not in st.session_state.scraped_data:
            results = st.session_state.scraped_data
            urls = list(results.keys())
            
            st.success(f"🎉 Crawl finished for {len(urls)} websites. Browse results below.")
            
            tabs = st.tabs([urlparse(u).netloc or u for u in urls])
            
            for i, url in enumerate(urls):
                with tabs[i]:
                    site_data = results[url].get("data", [])
                    site_error = results[url].get("error", None)
                    page_errors = results[url].get("page_errors", [])
                    
                    if site_error:
                        st.warning(f"Issues encountered during crawl: {site_error}")
                        
                    if not site_data:
                        st.info("No data extracted for this URL.")
                    else:
                        st.markdown(f"✅ **Extracted {len(site_data)} items.**")
                        
                        json_string = json.dumps(site_data, indent=4)
                        csv_data = pd.DataFrame(site_data).to_csv(index=False).encode('utf-8')
                        
                        domain = urlparse(url).netloc.replace(".", "_")
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            st.download_button(
                                label="📥 Download JSON",
                                data=json_string,
                                file_name=f"{domain}_data.json",
                                mime="application/json",
                                use_container_width=True,
                                key=f"json_{i}"
                            )
                        with c2:
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv_data,
                                file_name=f"{domain}_data.csv",
                                mime="text/csv",
                                use_container_width=True,
                                key=f"csv_{i}"
                            )
                            
                        st.markdown("#### Data Preview")
                        st.dataframe(pd.DataFrame(site_data), width='stretch', height=400)
                    
                    if page_errors:
                        st.markdown("---")
                        st.markdown("#### ⚠️ Error Logs")
                        st.info(f"Failed to fetch {len(page_errors)} pages from this site.")
                        
                        err_df = pd.DataFrame(page_errors)
                        domain = urlparse(url).netloc.replace(".", "_")
                        err_csv = err_df.to_csv(index=False).encode('utf-8')
                        
                        st.download_button(
                            label="📥 Download Error Logs (CSV)",
                            data=err_csv,
                            file_name=f"{domain}_errors.csv",
                            mime="text/csv",
                            use_container_width=True,
                            key=f"err_csv_{i}"
                        )
                        st.dataframe(err_df, width='stretch', height=250)


def guide_page():
    st.title("📖 User Guide")
    st.markdown("""
    Welcome to the UTeM Web Crawler tool! Follow these steps to collect data for your AI models:
    
    ### 1. Select Target Portals
    - In the **Crawler** page, use the dropdown to select a UTeM portal URL (e.g., `https://faix.utem.edu.my/`).
    - If your desired portal is not listed, choose **Custom URL...** and enter it manually.
    - Click **➕ Add URL** to add it to your crawl queue.
    - You can queue as many portals as you want. They will be crawled simultaneously.
    
    ### 2. Configure Limits
    - **Max Pages per site:** Set a limit to prevent the crawler from running indefinitely. (Default is 200).
    - **Advanced Options:** Define URL paths to ignore (e.g., login pages or admin panels).
    
    ### 3. Start Crawling
    - Click **🚀 Start Crawling Queue**.
    - The crawler will process all queued websites in parallel. Please be patient, as fetching hundreds of pages takes time.
    
    ### 4. Review & Export
    - Once completed, you can review the extracted text in the **Data Preview** section.
    - The results are split into **Tabs** for each website.
    - In each tab, you can individually export that website's data via the **Download JSON** or **Download CSV** buttons!
    """)


# Navigation Setup (Requires Streamlit >= 1.36)
with st.sidebar:
    st.info("UTeM Tuah RAG - Data Collection Tool")
    
pg = st.navigation([
    st.Page(crawler_page, title="Crawler", icon="🕷️"),
    st.Page(guide_page, title="User Guide", icon="📖")
])
pg.run()