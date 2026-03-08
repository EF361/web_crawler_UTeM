import streamlit as st
import json
import pandas as pd
from scraper_raw import scrape_multiple_pages

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
    initial_sidebar_state="collapsed"
)

# 2. Setup App Memory (Session State)
if "scraped_data" not in st.session_state:
    st.session_state.scraped_data = None
if "final_filename" not in st.session_state:
    st.session_state.final_filename = "data.json"

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

# 4. Main Layout
left_panel, right_panel = st.columns([1, 2], gap="large")

with left_panel:
    st.title("🕷️ Web Crawler")
    st.write("") 
    
    # Dropdown menu for UTeM portals
    selected_site = st.selectbox("🎯 Select Target UTeM Portal:", list(UTEM_URLS.keys()) + ["Custom URL..."])
    
    # Handle custom URL input
    if selected_site == "Custom URL...":
        url_input = st.text_input("🌐 Enter Custom URL:", "https://")
        default_filename = "crawler_data.json"
    else:
        url_input = UTEM_URLS[selected_site]
        # Automatically generate a clean filename based on the selection (e.g., FAIX_data.json)
        default_filename = f"{selected_site.split(' ')[0]}_data.json"
        
    max_pages_input = st.number_input("📄 Max Pages to Crawl:", min_value=1, value=200)
    
    with st.expander("🛠️ Advanced Options", expanded=False):
        ignore_input = st.text_input("🚫 Ignore URLs containing:", "contact, login, register, admin")
        filename_input = st.text_input("💾 Save file as:", default_filename)
    
    start_crawling = st.button("🚀 Start Crawling", type="primary", use_container_width=True)

with right_panel:
    # Trigger the crawling process
    if start_crawling:
        # Clear old memory before starting a new crawl
        st.session_state.scraped_data = None 
        
        ignore_list = [word.strip() for word in ignore_input.split(',')]
        
        if not filename_input.endswith(".json"):
            filename_input += ".json"
            
        with st.status("🤖 Crawler is working...", expanded=True) as status:
            st.write(f"Connecting to {url_input}...")
            st.write(f"Scraping up to {max_pages_input} pages...")
            
            scraped_data, error_msg = scrape_multiple_pages(url_input, max_pages_input, ignore_list)
            
            if error_msg:
                status.update(label="Crawling Failed", state="error", expanded=True)
                st.error(error_msg)
            elif not scraped_data:
                status.update(label="No Data Found", state="warning", expanded=True)
                st.warning("Crawling finished, but no useful text was found.")
            else:
                status.update(label="Crawling Complete!", state="complete", expanded=False)
                # Save the successful data to the app's memory
                st.session_state.scraped_data = scraped_data
                st.session_state.final_filename = filename_input

    # Display the results if they exist in memory (survives screen refreshes)
    if st.session_state.scraped_data:
        data = st.session_state.scraped_data
        filename = st.session_state.final_filename
        
        st.success(f"🎉 Success! Extracted {len(data)} clean items ready for AI.")
        
        json_string = json.dumps(data, indent=4)
        csv_data = pd.DataFrame(data).to_csv(index=False).encode('utf-8')
        
        # Side-by-Side Download Buttons
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            st.download_button(
                label="📥 Download JSON",
                data=json_string,
                file_name=filename,
                mime="application/json",
                use_container_width=True
            )
        with btn_col2:
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=filename.replace(".json", ".csv"),
                mime="text/csv",
                use_container_width=True
            )
        
        # Clean Tabbed Preview
        st.markdown("### Data Preview")
        tab1, tab2 = st.tabs(["📊 Table View", "💻 Raw JSON View"])
        with tab1:
            st.dataframe(pd.DataFrame(data), width='stretch', height=400)
        with tab2:
            st.json(data)