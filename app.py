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
    page_title="Lights & Travel ELD Analyzer",
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
    st.title("Lights & Travel ELD Analyzer")
    st.markdown("## 🔐 Login Required")
    st.write("Please enter your credentials to access the ELD Analyzer")
    
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
st.title("🚛 Lights & Travel ELD Analyzer")
st.write("Analyze ELD driver status, truck assignment conflicts, and username standards.")

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

def create_admin_tag_dataframe(filtered_data):
    """Create DataFrame for Excel export"""
    excel_data = []
    
    for item in filtered_data:
        vehicle = item.get('Vehicle', {}) or {}
        excel_data.append({
            'adminTagName': vehicle.get('DisplayID', ''),
        })
    
    return pd.DataFrame(excel_data)


def create_excel_file(dataframe):
    """Create Excel file in memory"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False, sheet_name='ELD Data')
    output.seek(0)
    return output

def get_first_initial(value):
    """Return the first non-empty character from a name field."""
    value = str(value or "").strip()
    return value[0].lower() if value else ""


def get_last_four_phone_digits(phone_number):
    """Return the last four numeric digits from a phone number."""
    digits = "".join(character for character in str(phone_number or "") if character.isdigit())
    return digits[-4:] if len(digits) >= 4 else ""


def build_expected_username(row):
    """Build username as phone last four digits + first initial + last initial."""
    return (
        get_last_four_phone_digits(row.get("Phone Number", ""))
        + get_first_initial(row.get("First Name", ""))
        + get_first_initial(row.get("Last Name", ""))
    )


def find_username_issues(drivers_df):
    """Find usernames that do not follow the L&T ELD username standard."""
    required_columns = ["First Name", "Last Name", "Phone Number", "Username", "Notes"]
    missing_columns = [column for column in required_columns if column not in drivers_df.columns]
    if missing_columns:
        return None, missing_columns, 0

    normalized_df = drivers_df.fillna("").copy()
    notes = normalized_df["Notes"].astype(str)
    exception_mask = notes.str.contains(r"\b(?:team|local)\b", case=False, na=False, regex=True)
    validation_df = normalized_df.loc[~exception_mask].copy()
    validation_df["Proposed Username"] = validation_df.apply(build_expected_username, axis=1)
    validation_df["Current Username"] = validation_df["Username"].astype(str).str.strip()

    issue_mask = (
        validation_df["Proposed Username"].ne("")
        & validation_df["Current Username"].str.lower().ne(validation_df["Proposed Username"])
    )
    issue_columns = [
        "First Name",
        "Last Name",
        "Phone Number",
        "Current Username",
        "Proposed Username",
        "Driver ID",
        "Email",
        "Notes",
    ]
    available_columns = [column for column in issue_columns if column in validation_df.columns]
    return validation_df.loc[issue_mask, available_columns], [], int(exception_mask.sum())


def render_status_report():
    st.markdown("### 📊 Driver Status Export")
    st.write("Export driver and truck data filtered by current status in L&T ELD.")

    status_buttons = [
        ("🚗 Driving", "Driving", "driving_drivers.xlsx"),
        ("😴 Off Duty", "Off Duty", "off_duty_drivers.xlsx"),
        ("⚡ On Duty", "On Duty", "on_duty_drivers.xlsx"),
        ("🛏️ SB", "SB", "sb_drivers.xlsx"),
    ]
    columns = st.columns(4)

    for column, (label, status, file_name) in zip(columns, status_buttons):
        with column:
            if st.button(label, use_container_width=True):
                with st.spinner("Fetching data from L&T ELD..."):
                    data = fetch_eld_data()
                    if not data:
                        return

                    filtered_data = filter_data_by_status(data, status)
                    if not filtered_data:
                        st.warning(f"No drivers found with {status} status")
                        return

                    df = create_excel_dataframe(filtered_data)
                    excel_file = create_excel_file(df)

                    st.success(f"Found {len(filtered_data)} drivers with {status} status")
                    st.download_button(
                        label=f"📥 Download {status} Report",
                        data=excel_file,
                        file_name=file_name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                    if status in ["Driving", "On Duty"]:
                        admin_tag_df = create_admin_tag_dataframe(filtered_data)
                        admin_tag_csv = admin_tag_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Admin Tag Report",
                            data=admin_tag_csv,
                            file_name=f"{status.lower().replace(' ', '_')}_admin_tags.csv",
                            mime="text/csv"
                        )


def render_vehicle_conflicts():
    st.markdown("### 🚨 Vehicle Conflict Finder")
    st.write("Find drivers who are assigned to the same vehicle in ELD.")

    if st.button("🔍 Find Vehicle Conflicts", use_container_width=True, type="secondary"):
        with st.spinner("Analyzing vehicle assignments for conflicts..."):
            try:
                sync = ELDSync(API_BASE_URL, ELD_API_KEY)
                drivers = sync.fetch_eld_drivers_sync()

                if not drivers:
                    st.error("Failed to fetch driver data from ELD system")
                    return

                incorrect_assignments = sync.find_vehicle_conflicts(drivers)
                if not incorrect_assignments:
                    st.success("✅ No vehicle conflicts found! All drivers are properly assigned.")
                    return

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
                st.dataframe(df_conflicts, use_container_width=True)

                excel_file = create_excel_file(df_conflicts)
                st.download_button(
                    label="📥 Download Vehicle Conflicts Report",
                    data=excel_file,
                    file_name="vehicle_conflicts.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error analyzing vehicle conflicts: {str(e)}")


def render_username_validator():
    st.markdown("### 🧾 Username Pattern Validator")
    st.write(
        "Upload the drivers CSV exported from the ELD dashboard. The expected username is "
        "`last four phone digits + first initial + last initial`."
    )
    st.caption('Drivers with "Team" or "local" in Notes are skipped as exceptions.')

    uploaded_file = st.file_uploader(
        "Upload ELD drivers CSV",
        type=["csv"],
        help="Use the drivers list CSV exported directly from the ELD dashboard."
    )

    if uploaded_file is None:
        return

    try:
        drivers_df = pd.read_csv(uploaded_file, dtype=str)
    except Exception as e:
        st.error(f"Could not read CSV file: {str(e)}")
        return

    username_issues, missing_columns, skipped_count = find_username_issues(drivers_df)
    if missing_columns:
        st.error(f"CSV is missing required columns: {', '.join(missing_columns)}")
        return

    st.info(f"Skipped {skipped_count} exception records with Team or local in Notes.")

    if username_issues.empty:
        st.success("✅ No username pattern issues found.")
        return

    st.warning(f"Found {len(username_issues)} drivers with incorrect usernames.")
    st.dataframe(username_issues, use_container_width=True)

    csv_file = username_issues.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Username Issues CSV",
        data=csv_file,
        file_name="username_pattern_issues.csv",
        mime="text/csv"
    )

    excel_file = create_excel_file(username_issues)
    st.download_button(
        label="📥 Download Username Issues Excel",
        data=excel_file,
        file_name="username_pattern_issues.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


status_tab, conflicts_tab, username_tab = st.tabs([
    "1. Driver Status",
    "2. Vehicle Conflicts",
    "3. Username Pattern"
])

with status_tab:
    render_status_report()

with conflicts_tab:
    render_vehicle_conflicts()

with username_tab:
    render_username_validator()

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