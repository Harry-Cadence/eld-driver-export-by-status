import streamlit as st
import requests
import pandas as pd
from io import BytesIO
import json
from dotenv import load_dotenv
import os
from duplicate import ELDDriver, ELDSync

# Configure Streamlit page
st.set_page_config(
    page_title="Export The List by ELD Status",
    page_icon="🚛",
    layout="centered"
)

# Simple login system
def check_login():
    """Simple login check using secrets or environment variables"""
    try:
        # Try to get credentials from Streamlit secrets (for cloud deployment)
        username = st.secrets.get("LOGIN_USERNAME", "admin")
        password = st.secrets.get("LOGIN_PASSWORD", "admin321")
    except:
        # Fallback for local development - use environment variables or defaults
        load_dotenv()
        username = os.getenv("LOGIN_USERNAME", "admin")
        password = os.getenv("LOGIN_PASSWORD", "admin321")
    
    return username, password

def login_page():
    """Display login form"""
    st.title("ELD Status Report Tool")
    st.markdown("## 🔐 Login Required")
    st.write("Please enter your credentials to access the ELD Status Export Tool")
    
    with st.form("login_form"):
        username_input = st.text_input("Username", key="username_input")
        password_input = st.text_input("Password", type="password", key="password_input")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            correct_username, correct_password = check_login()
            if username_input == correct_username and password_input == correct_password:
                st.session_state.authenticated = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")

# Check if user is authenticated
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Show login page if not authenticated
if not st.session_state.authenticated:
    login_page()
    st.stop()

# Main app content (only shown after successful login)
st.title("🚛 Export The List by ELD Status")
st.write("Export driver and truck data filtered by current status in L&T ELD")

# Add logout button
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.rerun()

load_dotenv()

try:
    API_BASE_URL = st.secrets["ELD_API_URL"]
    ELD_API_KEY = st.secrets.get("ELD_API_KEY")  
except:
    # Fallback for local development
    API_BASE_URL = os.getenv("ELD_API_URL")
    ELD_API_KEY = os.getenv("ELD_API_KEY")

API_ENDPOINT = "api/v1/driver/eld/"

# Status mapping
STATUS_OPTIONS = ['Driving', 'Off Duty', 'On Duty', 'SB']

def fetch_eld_data():
    """Fetch ELD data from API"""
    try:
        url = f"{API_BASE_URL}{API_ENDPOINT}"
        eld_headers = {
        'X-Api-Key': ELD_API_KEY,
        'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=eld_headers, timeout=30)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        return None
    except json.JSONDecodeError:
        st.error("Invalid JSON response from API")
        return None

def filter_data_by_status(data, status):
    """Filter data by current status"""
    if not data or 'Data' not in data:
        return []
    
    filtered_data = []
    for item in data['Data']:
        if item.get('Log', {}).get('CurrentStatus') == status:
            filtered_data.append(item)
    
    return filtered_data

def create_excel_dataframe(filtered_data):
    """Create DataFrame for Excel export"""
    excel_data = []
    
    for item in filtered_data:
        driver = item.get('Driver', {}) or {}
        vehicle = item.get('Vehicle', {}) or {}
        log = item.get('Log', {}) or {}
        
        excel_data.append({
            'First Name': driver.get('FirstName', ''),
            'Last Name': driver.get('LastName', ''),
            'Phone Number': driver.get('PhoneNo', ''),
            'Vehicle Display ID': vehicle.get('DisplayID', ''),
            'Log Status': log.get('CurrentStatus', '')
        })
    
    return pd.DataFrame(excel_data)

def create_excel_file(dataframe):
    """Create Excel file in memory"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False, sheet_name='ELD Data')
    output.seek(0)
    return output

# Create columns for buttons
col1, col2, col3, col4 = st.columns(4)

# Button handlers
with col1:
    if st.button("🚗 Driving", use_container_width=True):
        with st.spinner("Fetching data from L&T ELD..."):
            data = fetch_eld_data()
            if data:
                filtered_data = filter_data_by_status(data, 'Driving')
                if filtered_data:
                    df = create_excel_dataframe(filtered_data)
                    excel_file = create_excel_file(df)
                    
                    st.success(f"Found {len(filtered_data)} drivers with Driving status")
                    st.download_button(
                        label="📥 Download Driving Report",
                        data=excel_file,
                        file_name="driving_drivers.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("No drivers found with Driving status")

with col2:
    if st.button("😴 Off Duty", use_container_width=True):
        with st.spinner("Fetching data from L&T ELD..."):
            data = fetch_eld_data()
            if data:
                filtered_data = filter_data_by_status(data, 'Off Duty')
                if filtered_data:
                    df = create_excel_dataframe(filtered_data)
                    excel_file = create_excel_file(df)
                    
                    st.success(f"Found {len(filtered_data)} drivers with Off Duty status")
                    st.download_button(
                        label="📥 Download Off Duty Report",
                        data=excel_file,
                        file_name="off_duty_drivers.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("No drivers found with Off Duty status")

with col3:
    if st.button("⚡ On Duty", use_container_width=True):
        with st.spinner("Fetching data from L&T ELD..."):
            data = fetch_eld_data()
            if data:
                filtered_data = filter_data_by_status(data, 'On Duty')
                if filtered_data:
                    df = create_excel_dataframe(filtered_data)
                    excel_file = create_excel_file(df)
                    
                    st.success(f"Found {len(filtered_data)} drivers with On Duty status")
                    st.download_button(
                        label="📥 Download On Duty Report",
                        data=excel_file,
                        file_name="on_duty_drivers.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("No drivers found with On Duty status")

with col4:
    if st.button("🛏️ SB", use_container_width=True):
        with st.spinner("Fetching data from L&T ELD..."):
            data = fetch_eld_data()
            if data:
                filtered_data = filter_data_by_status(data, 'SB')
                if filtered_data:
                    df = create_excel_dataframe(filtered_data)
                    excel_file = create_excel_file(df)
                    
                    st.success(f"Found {len(filtered_data)} drivers with SB status")
                    st.download_button(
                        label="📥 Download SB Report",
                        data=excel_file,
                        file_name="sb_drivers.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("No drivers found with SB status")

# Add spacing between sections
st.markdown("---")

# New section for vehicle conflicts
st.markdown("### 🚨 List of Multiple Drivers Logged into Same Truck in ELD")
st.write("Check for drivers who are assigned to the same vehicle (potential conflicts). Click below for list.")

# Long button for vehicle conflicts
if st.button("🔍 Find Vehicle Conflicts", use_container_width=True, type="secondary"):
    with st.spinner("Analyzing vehicle assignments for conflicts..."):
        try:
            # Create ELDSync instance
            sync = ELDSync(API_BASE_URL, ELD_API_KEY)
            
            # Fetch all drivers synchronously (better for Streamlit)
            drivers = sync.fetch_eld_drivers_sync()
            
            if drivers:
                # Find conflicts
                incorrect_assignments = sync.find_vehicle_conflicts(drivers)
                
                if incorrect_assignments:
                    # Create DataFrame for display
                    conflict_data = []
                    for driver in incorrect_assignments:
                        conflict_data.append({
                            'Driver ID': driver.driverID,
                            'First Name': driver.firstName,
                            'Last Name': driver.lastName,
                            'Phone Number': driver.phoneNo,
                            'Truck Number': driver.truckNo,
                            'Drivers on Same Truck': driver.truckCount
                        })
                    
                    df_conflicts = pd.DataFrame(conflict_data)
                    
                    st.success(f"Found {len(incorrect_assignments)} drivers with vehicle conflicts!")
                    
                    # Display the conflicts table
                    st.dataframe(df_conflicts, use_container_width=True)
                    
                    # Create Excel file for download
                    excel_file = create_excel_file(df_conflicts)
                    st.download_button(
                        label="📥 Download Vehicle Conflicts Report",
                        data=excel_file,
                        file_name="vehicle_conflicts.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.success("✅ No vehicle conflicts found! All drivers are properly assigned.")
            else:
                st.error("Failed to fetch driver data from ELD system")
                
        except Exception as e:
            st.error(f"Error analyzing vehicle conflicts: {str(e)}")

# Add some spacing and information
# st.markdown("---")
# st.markdown("""
# ### 📋 Export Information
# - **First Name**: Driver's first name
# - **Last Name**: Driver's last name  
# - **Phone Number**: Driver's contact number
# - **Vehicle Display ID**: Vehicle identifier
# - **Log Status**: Current driver status

# ### 🔧 Setup Instructions
# 1. Replace `API_BASE_URL` with your actual API base URL
# 2. Add authentication headers if required
# 3. Install required packages: `pip install streamlit pandas requests openpyxl`
# 4. Run with: `streamlit run app.py`
# """)

# # Optional: Display current API status
# with st.expander("🔍 API Status Check"):
    # if st.button("Test API Connection"):
    #     with st.spinner("Testing connection..."):
    #         try:
    #             url = f"{API_BASE_URL}{API_ENDPOINT}"
    #             eld_headers = {
    #             'X-Api-Key': ELD_API_KEY,
    #             'Content-Type': 'application/json'
    #             }
    #             response = requests.get(url, headers=eld_headers)
    #             if response.status_code == 200:
    #                 st.success("✅ API connection successful")
    #                 data = response.json()
    #                 if 'Data' in data:
    #                     st.info(f"📊 Total records available: {len(data['Data'])}")
    #             else:
    #                 st.error(f"❌ API returned status code: {response.status_code}")
    #         except Exception as e:
    #             st.error(f"❌ Connection failed: {str(e)}")