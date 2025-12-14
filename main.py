import streamlit as st
import base64
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# --- PAGE CONFIG (Must be first) ---
st.set_page_config(page_title="Data Palette", layout="wide")

# ==========================================
# GOOGLE DRIVE CONFIGURATION
# ==========================================
# 1. Open the folder/file in Google Drive.
# 2. Look at the URL. 
#    Folder: .../drive/folders/YOUR_ID_HERE
#    File: .../file/d/YOUR_ID_HERE/view

DRIVE_FOLDER_ID_HEXBIN = "1Jo8J3dCrfFlCWBpuA6S6LuSBEZlYWQiz"
DRIVE_FOLDER_ID_RATIO = "1OJEmNqsypkt2zSNn7GFM_TB0bHOtnxwA"
FILE_ID_NAMES_TXT = "1absVXCyBftpjuYQYY9yWDOBD55REXJHb"
FILE_ID_NAMES2_TXT = "1ISKIsGYcA9uV0Xd5eAaScHW5e_0zW38r"

# ==========================================
# GOOGLE DRIVE API FUNCTIONS
# ==========================================

@st.cache_resource
def get_drive_service():
    """Authenticates using Streamlit secrets."""
    try:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"Authentication Error: Please check .streamlit/secrets.toml. {e}")
        return None

@st.cache_data(ttl=3600)
def get_drive_file_map(folder_id):
    """
    Returns a dictionary {filename: file_id} for all files in a folder.
    Cached for 1 hour to speed up the app.
    """
    service = get_drive_service()
    if not service: return {}
    
    files_dict = {}
    page_token = None
    
    try:
        while True:
            results = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="nextPageToken, files(id, name)",
                pageToken=page_token
            ).execute()
            
            items = results.get('files', [])
            for item in items:
                files_dict[item['name']] = item['id']
                
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        return files_dict
    except Exception as e:
        st.error(f"Error listing files from Drive: {e}")
        return {}

@st.cache_data(ttl=3600)
def read_txt_from_drive(file_id):
    """Downloads a text file and returns a list of lines."""
    service = get_drive_service()
    if not service: return []
    
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        content = fh.getvalue().decode('utf-8')
        return content.splitlines()
    except Exception as e:
        st.error(f"Error reading text file: {e}")
        return []

def get_image_base64_from_drive(file_id):
    """Downloads an image into memory and returns base64 string."""
    service = get_drive_service()
    if not service: return None
    
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        return base64.b64encode(fh.getvalue()).decode()
    except Exception as e:
        st.error(f"Error downloading image: {e}")
        return None

# ==========================================
# ORIGINAL HELPER FUNCTIONS (Refactored for Drive)
# ==========================================

@st.cache_data
def load_data_structure_drive(file_id):
    data_map = {}
    lines = read_txt_from_drive(file_id)
    
    if not lines: return None
    
    for line in lines:
        filename = line.strip()
        if not filename.endswith(".png"): continue
        try:
            # Parse assuming single underscore delimiters first
            parts = filename.split("_filter")
            vars_main = parts[0].split("vs")
            
            # STRIP underscores to get clean names (The Fix)
            var1 = vars_main[0].strip("_") 
            var2 = vars_main[1].strip("_")
            
            filter_part = parts[1] # e.g. "_df1_INCOME_bin_ge_0"
            filter_var = filter_part.split("_bin_ge")[0].strip("_")

            if var1 not in data_map: data_map[var1] = {}
            if var2 not in data_map[var1]: data_map[var1][var2] = []
            if filter_var not in data_map[var1][var2]: data_map[var1][var2].append(filter_var)
        except: continue
    return data_map

# ==========================================
# MAPPING DICTIONARY
# ==========================================

VARIABLE_MAPPINGS = {
"df1_AMT_ANNUITY": "Loan Annuity",
"df1_AMT_CREDIT": "Credit Amount",
"df1_AMT_INCOME_TOTAL": "Total Income",
"df1_AMT_REQ_CREDIT_BUREAU_MON": "Credit Bureau Enquiries (Monthly)",
"df1_APARTMENTS_AVG": "Average Apartment Size",
"df1_DAYS_BIRTH": "Age (Days)",
"df1_DAYS_EMPLOYED": "Days Employed",
"df1_DAYS_LAST_PHONE_CHANGE": "Days Since Last Phone Change",
"df1_DAYS_REGISTRATION": "Registration Days",
"df1_CODE_GENDER": "Gender",
"df1_FLAG_OWN_CAR": "Car Ownership",
"df1_FLAG_OWN_REALTY": "Realty Ownership",
"df1_CNT_CHILDREN": "Child Count",
"df1_NAME_EDUCATION_TYPE": "Education Level",
"df1_NAME_FAMILY_STATUS": "Family Status",
"df1_NAME_HOUSING_TYPE": "Housing Type",
"df1_NAME_INCOME_TYPE": "Income Type",
"df1_OCCUPATION_TYPE": "Occupation",
"df1_ORGANIZATION_TYPE": "Organization Type",
"df1_EXT_SOURCE_1": "External Source 1",
"df1_EXT_SOURCE_2": "External Source 2",
"df1_EXT_SOURCE_3": "External Source 3"
}

# ==========================================
# CUSTOM CSS
# ==========================================

st.markdown("""
<style>
    /* 1. GLOBAL FONT RESET TO GARAMOND */
    html, body, [class*="css"] {
        font-family: 'Garamond', 'Georgia', serif;
    }
    
    /* Force Streamlit specific elements to use Garamond */
    .stSelectbox, .stSlider, .stMarkdown, .stText, .stHtml, .stAlert, .stButton {
        font-family: 'Garamond', 'Georgia', serif !important;
    }
    
    /* General Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Garamond', 'Georgia', serif !important;
        color: #111827;
        font-weight: 600;
        margin-bottom: 0.2rem !important;
    }
    
    p, li, span, div {
        font-family: 'Garamond', 'Georgia', serif;
        color: #374151;
        line-height: 1.35; 
        font-size: 17px;   
    }

    /* --- ATTRIBUTE INTUITION (INFO BOX) FIX --- */
    .stAlert p, .stAlert span, .stAlert div {
        font-size: 15px !important;
        line-height: 1.3 !important;
    }
    .stAlert > div {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }

    /* APP CONTAINER STYLING */
    [data-testid="stAppViewContainer"] {
        background-color: #ffffff;
    }
    
    .block-container {
        padding-top: 3rem !important; 
        padding-bottom: 2rem !important;
        max-width: 95% !important; 
    }
    
    /* --- SIDEBAR SPACING FIXES --- */
    [data-testid="stSidebarContent"] {
        display: flex;
        flex-direction: column;
        padding-top: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    [data-testid="stSidebarNav"] {
        order: 2; 
        border-top: 1px solid #e5e7eb;
        padding-top: 10px;
        margin-top: 10px;
    }
    [data-testid="stSidebarUserContent"] {
        order: 1;
        padding-bottom: 0px;
    }
    
    /* Sidebar Title Styles */
    .sidebar-title {
        font-family: 'Garamond', serif;
        font-size: 24px;
        font-weight: 700;
        color: #000;
        margin-top: 0px !important;
        margin-bottom: 0px;
        line-height: 1.1;
    }
    .sidebar-caption {
        font-family: 'Garamond', serif;
        font-size: 14px;
        font-weight: 400;
        color: #666;
        margin-bottom: 10px;
        font-style: italic;
    }

    /* --- DROPDOWN & LABEL EQUALITY --- */
    [data-testid="stWidgetLabel"] p {
        font-size: 15px !important;
        font-weight: 600 !important;
        margin-bottom: 2px !important;
    }

    div[data-baseweb="select"] span, div[data-baseweb="select"] div {
        font-size: 15px !important;
    }

    div[data-baseweb="select"] > div {
        min-height: 36px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        display: flex;
        align-items: center; 
    }

    /* Animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Images */
    .fade-in-image {
        animation: fadeIn 0.6s ease-out;
        width: 100%;
        border-radius: 2px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #e5e7eb;
        margin-bottom: 10px;
    }

    .fade-in-image-small {
        animation: fadeIn 0.6s ease-out;
        width: 65%;
        display: block;
        margin-left: auto;
        margin-right: auto;
        border-radius: 2px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #e5e7eb;
    }

    /* Team Cards */
    .team-card {
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 15px; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        height: 100%;
        min-height: 220px; 
        display: flex;
        flex-direction: column;
    }
    .team-card:hover {
        border-color: #3b82f6;
    }
    .member-name {
        font-family: 'Garamond', serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: #000;
        margin-bottom: 0.1rem;
    }
    .member-role {
        font-family: 'Garamond', serif;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #3b82f6;
        margin-bottom: 0.4rem;
    }
    
    /* --- DASHBOARD HEADERS --- */
    .axis-subheading {
        font-family: 'Garamond', serif;
        color: #000;
        font-size: 28px;
        font-weight: 700;
        display: flex;
        flex-direction: row;
        flex-wrap: wrap; 
        justify-content: center;
        align-items: center;
        column-gap: 15px; 
        margin-top: 20px; 
        padding-top: 10px;
        margin-bottom: 20px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        line-height: 1.2;
    }
    .vs-tag {
        font-family: 'Garamond', serif;
        color: #555;
        font-size: 22px;
        font-weight: 400;
        text-transform: lowercase;
        font-style: italic;
        white-space: nowrap; 
    }
</style>
""", unsafe_allow_html=True)

# --- FORMATTING FUNCTION ---

def format_label(label):
    """
    1. Checks if label is in VARIABLE_MAPPINGS.
    2. If not, removes 'df1_' and replaces '_' with space.
    """
    if not label: return ""
    
    # Check specific mapping
    if label in VARIABLE_MAPPINGS:
        return VARIABLE_MAPPINGS[label]
        
    # Generic fallback
    return label.replace("df1_", "").replace("_", " ").title()

# ==========================================
# PAGE DEFINITIONS
# ==========================================

def page_introduction():
    st.title("The Planner vs The Impulsive Borrower")
    
    st.markdown("""
    ### Introduction
    **Transforming Raw Data into Visual Harmony**
    
    Just as an artist meticulously selects colors from a palette to create a masterpiece, our project team **Data Palette**—aims to transform unorganized, raw data into beautifully coherent visual narratives. 
    
    This project is presented by students of the **IIT Madras BS in Data Science** program for the course **Data Visualization Design (BSCS4001)**, Term 3, 2025.
    """)
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("The Analogy: From Chaos to Composition")
        st.markdown("""
        A painter's palette contains infinite possibilities. Similarly, data in its raw form is like pigment scattered without direction. 
        Our mission is to apply the principles of design, aesthetics, and human perception to create visualizations that:
        *   **Transform chaos into clarity**
        *   **Reveal hidden stories**
        *   **Engage audiences**
        *   **Create beauty in information**
        """)
    with col2:
        st.info("Design Philosophy: Functionality and Aesthetics are not mutually exclusive.")
    
    st.markdown("---")
    st.subheader("Meet the Team")
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.markdown("""<div class="team-card"><div class="member-name">Gurneet Kaur Bhuller</div> [DS - 21F2000672]<div class="member-role">Team Leader</div><div class="member-desc">Leading with strategic vision and design oversight.</div></div>""", unsafe_allow_html=True)
    with t2:
        st.markdown("""<div class="team-card"><div class="member-name">Atharva Dhamankar</div> [DS - 21F1005520]<div class="member-role">Backend & Data</div><div class="member-desc">Handling data transformation and architectural decisions.</div></div>""", unsafe_allow_html=True)
    with t3:
        st.markdown("""<div class="team-card"><div class="member-name">Sankalp Kundu</div> [DS - 21F1002742]<div class="member-role">Data Analysis</div><div class="member-desc">Extracting meaningful patterns and identifying trends.</div></div>""", unsafe_allow_html=True)
    with t4:
        st.markdown("""<div class="team-card"><div class="member-name">Harsh Patil</div> [DS - 21F1002234]<div class="member-role">Frontend & Interaction</div><div class="member-desc">Crafting the user interface and interactive elements.</div></div>""", unsafe_allow_html=True)

def page_problem_statement():
    st.title("Problem Statement")
    st.subheader("The Core Objective")
    st.markdown("""
    As an analyst for a finance company, our primary goal is to improve the applicant evaluation process for loans to:
    1.  Reduce financial losses from loan defaults.
    2.  Grow its loan portfolio by safely approving more trustworthy applicants.
    """)
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.warning("Risk of Approving a Defaulter: Recovery costs, delayed payments, potential capital loss.")
    with col2:
        st.info("Risk of Rejecting a Good Applicant: Missed revenue, lost valuable customers, slower growth.")
    st.markdown("---")
    st.success("Final Goal: Empower the credit team to make cleaner, data-driven decisions.")

def page_dashboard():
    # --- INSIGHTS DICTIONARY ---
    attribute_descriptions = {
        "df1_AMT_ANNUITY": "It is generally observed that individuals who tend to pay higher annuity, tend to default less frequently.",
        "df1_APARTMENTS_AVG": "It is generally observed that individuals who have live in areas with high apartment sizes on average , tend to default less frequently.",
        "df1_DAYS_EMPLOYED": "It is generally observed that individuals who have changed their jobs quite long before they apply for a loan, tend to default less frequently.",
        "df1_DAYS_LAST_PHONE_CHANGE": "It is generally observed that individuals who have changed their phone numbers around 5+ years ago before applying, tend to default less frequently.",
        "df1_AMT_CREDIT": "It is generally observed that individuals who tend to request and recieve high credit amounts for their loans, tend to default less frequently.",
        "df1_AMT_INCOME_TOTAL": "It is generally observed that individuals who tend to have higher total incomes, tend to default less frequently.",
        "df1_AMT_REQ_CREDIT_BUREAU_MON": "It is generally observed that individuals who tend to check their credit scores high number of times within a month, tend to default less frequently.",
        "df1_DAYS_BIRTH": "It is generally observed that individuals who are born earlier, tend to default less frequently but the margin is quite less.",
        "df1_DAYS_REGISTRATION": "It is generally observed that individuals who have changed their registrations long before applying for a loan, tend to default less frequently."
    }

    # 1. Load Data Structure from DRIVE
    data_map = load_data_structure_drive(FILE_ID_NAMES_TXT)
    
    # 2. Pre-fetch file list from Hexbin Folder (Cached)
    image_files_map = get_drive_file_map(DRIVE_FOLDER_ID_HEXBIN)

    if data_map is None:
        st.error(f"❌ Error: Could not load 'names.txt' from Google Drive.")
    elif not data_map:
        st.error(f"❌ Error: 'names.txt' was found but could not parse data.")
    else:
        with st.sidebar:
            st.header("Graph Controls")
            
            # --- PAGE 1 DROPDOWNS ---
            var1 = st.selectbox("X-Axis Variable", sorted(list(data_map.keys())), format_func=format_label)
            var2 = st.selectbox("Y-Axis Variable", sorted(list(data_map[var1].keys())), format_func=format_label)
            filt = st.selectbox("Filter Variable", sorted(data_map[var1][var2]), format_func=format_label)
            bin_val = st.slider("Bin Threshold", 0, 9, 0)

        # Display Heading
        dy = format_label(var1)
        dx = format_label(var2)
        
        st.markdown(f'''
            <div class="axis-subheading">
                <span>{dy}</span> 
                <span class="vs-tag">vs</span> 
                <span>{dx}</span>
            </div>
        ''', unsafe_allow_html=True)

        # --- LEGEND ---
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""<div style="text-align: center; margin-bottom: 5px;"><span style="background-color: #e3f2fd; padding: 4px 15px; border-radius: 12px; border: 1px solid #90caf9; color: #1565c0; font-size: 14px;">● <b>Non-Defaulters</b> (Blue)</span></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("""<div style="text-align: center; margin-bottom: 5px;"><span style="background-color: #ffebee; padding: 4px 15px; border-radius: 12px; border: 1px solid #ef9a9a; color: #c62828; font-size: 14px;">● <b>Loan Defaulters</b> (Red)</span></div>""", unsafe_allow_html=True)

        filename = f"{var1}_vs_{var2}__filter_{filt}_bin_ge_{bin_val}.png"
        
        
        # Check if file exists in our Drive Map
        if filename in image_files_map:
            # Fetch the actual image using ID
            img_id = image_files_map[filename]
            img_str = get_image_base64_from_drive(img_id)
            
            if img_str:
                st.markdown(f'<img src="data:image/png;base64,{img_str}" class="fade-in-image">', unsafe_allow_html=True)
            
            # --- ATTRIBUTE INTUITION ---
            has_v1_info = var1 in attribute_descriptions
            has_v2_info = var2 in attribute_descriptions

            if has_v1_info or has_v2_info:
                st.markdown("### Attribute Intuition")
                if has_v1_info:
                    st.info(f"**{format_label(var1)}**: {attribute_descriptions[var1]}")
                if has_v2_info and var1 != var2:
                    st.info(f"**{format_label(var2)}**: {attribute_descriptions[var2]}")

        else:
            st.warning(f"Graph not found.")
            st.info(f"Looking for: {filename}")

def page_ratio_dashboard():
    # 1. Load Data Structure from DRIVE
    data_map = load_data_structure_drive(FILE_ID_NAMES2_TXT)
    
    # 2. Pre-fetch file list from Ratio Folder (Cached)
    image_files_map = get_drive_file_map(DRIVE_FOLDER_ID_RATIO)

    if data_map is None:
        st.error(f"❌ Error: Could not load 'names2.txt' from Google Drive.")
    elif not data_map:
        st.error(f"❌ Error: 'names2.txt' parsed no data.")
    else:
        with st.sidebar:
            st.header("Ratio Controls")
            
            # --- PAGE 2 DROPDOWNS ---
            var1 = st.selectbox("X-Axis Variable", sorted(list(data_map.keys())), key="r_v1", format_func=format_label)
            var2 = st.selectbox("Y-Axis Variable", sorted(list(data_map[var1].keys())), key="r_v2", format_func=format_label)
            filt = st.selectbox("Filter Variable", sorted(data_map[var1][var2]), key="r_f", format_func=format_label)
            bin_val = st.slider("Bin Threshold", 0, 9, 0, key="r_b")
        
        dy = format_label(var1)
        dx = format_label(var2)
        
        st.markdown(f'''
            <div class="axis-subheading">
                <span>{dy}</span> 
                <span class="vs-tag">vs</span> 
                <span>{dx}</span>
            </div>
        ''', unsafe_allow_html=True)

        filename = f"{var1}_vs_{var2}__filter_{filt}_bin_ge_{bin_val}_ratio.png"
        # Check and Download
        if filename in image_files_map:
            img_id = image_files_map[filename]
            img_str = get_image_base64_from_drive(img_id)
            
            if img_str:
                st.markdown(f'<img src="data:image/png;base64,{img_str}" class="fade-in-image-small">', unsafe_allow_html=True)
        else:
            st.warning(f"Graph not found.")
            st.info(f"Looking for: {filename}")

# ==========================================
# MAIN NAVIGATION & SIDEBAR SETUP
# ==========================================

# 1. SIDEBAR TITLE
with st.sidebar:
    st.markdown('<div class="sidebar-title">Data Palette</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-caption">DVD | Sept \'25 | CS4001</div>', unsafe_allow_html=True)

# 2. PAGE NAVIGATION
intro_pg = st.Page(page_introduction, title="Introduction")
problem_pg = st.Page(page_problem_statement, title="Problem Statement")
dashboard_pg = st.Page(page_dashboard, title="Defaulters Vs Non Defaulters")
ratio_pg = st.Page(page_ratio_dashboard, title="Islands of Stability")

pg = st.navigation([intro_pg, problem_pg, dashboard_pg, ratio_pg])

pg.run()