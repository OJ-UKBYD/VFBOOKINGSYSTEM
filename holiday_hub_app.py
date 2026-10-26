import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os

# --- APP CONFIGURATION ---
st.set_page_config(
    page_title="Family & Friends Holiday Hub",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FILE PATHS FOR STORAGE ---
BOOKINGS_FILE = "holiday_bookings.csv"
SETTINGS_FILE = "hub_settings.json"

# --- DEFAULT CONFIGURATION SETTINGS ---
DEFAULT_SETTINGS = {
    "property_address": "123 Ocean Breeze Lane, Paradise Valley",
    "key_code": "4829#",
    "directions": "Take Exit 45 from the coastal highway. Turn right at the marina. The villa is the third house on the left with the blue door.",
    "check_in_time": "15:00",
    "check_out_time": "11:00"
}

# --- DATA INITIALISATION ENGINES ---
def load_bookings():
    if os.path.exists(BOOKINGS_FILE):
        try:
            df = pd.read_csv(BOOKINGS_FILE)
            df['Check-In'] = pd.to_datetime(df['Check-In']).dt.date
            df['Check-Out'] = pd.to_datetime(df['Check-Out']).dt.date
            return df
        except Exception:
            return create_empty_bookings_df()
    return create_empty_bookings_df()

def create_empty_bookings_df():
    return pd.DataFrame(columns=[
        'Booking ID', 'Guest Name', 'Check-In', 'Check-Out', 
        'Email', 'Phone', 'Arrival Flight', 'Return Flight', 'Notes'
    ])

def save_bookings(df):
    df.to_csv(BOOKINGS_FILE, index=False)

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_SETTINGS
    return DEFAULT_SETTINGS

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

# Load persistent states
if 'bookings' not in st.session_state:
    st.session_state.bookings = load_bookings()

if 'settings' not in st.session_state:
    st.session_state.settings = load_settings()

if 'logs' not in st.session_state:
    st.session_state.logs = []

# --- CORE OVERLAP CHECKER ENGINE ---
def check_overlap(new_in, new_out):
    df = st.session_state.bookings
    if df.empty:
        return False, []
    
    overlaps = []
    for _, row in df.iterrows():
        exist_in = row['Check-In']
        exist_out = row['Check-Out']
        
        # Overlap rules: Strict overnight collision tracker. 
        # Same-day check-in/out transitions (exist_out == new_in or exist_in == new_out) are valid.
        if new_in < exist_out and new_out > exist_in:
            overlaps.append(f"{row['Guest Name']} ({exist_in} to {exist_out})")
            
    if overlaps:
        return True, overlaps
    return False, []

# --- VIEW CONTROLLER SIDEBAR ---
st.sidebar.title("🏡 Holiday Hub Navigation")
page = st.sidebar.radio("Go to:", ["📅 Dashboard & Summary", "➕ New Booking Request", "⚙️ Hub Properties"])

# --- PAGE 1: DASHBOARD & SUMMARY ---
if page == "📅 Dashboard & Summary":
    st.title("📅 Dashboard & Booking Timeline")
    
    # Quick Statistics Row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Reserved Bookings", len(st.session_state.bookings))
    with col2:
        upcoming = 0
        if not st.session_state.bookings.empty:
            upcoming = len(st.session_state.bookings[st.session_state.bookings['Check-In'] >= datetime.today().date()])
        st.metric("Upcoming Trips", upcoming)
    with col3:
        st.metric("Property Hub Status", "Active ✅")

    st.subheader("🗓️ Property Availability Calendar Matrix")
    
    # Calendar Filter Controls
    today = datetime.today().date()
    start_of_month = today.replace(day=1)
    
    col_cal1, col_cal2 = st.columns([1, 3])
    with col_cal1:
        cal_start = st.date_input("Calendar Start View", start_of_month)
        days_to_show = st.slider("Days to Display", min_value=14, max_value=90, value=35)
        cal_end = cal_start + timedelta(days=days_to_show)
    
    # Generate Date Matrix Range
    date_range = [cal_start + timedelta(days=x) for x in range((cal_end - cal_start).days + 1)]
    
    # Grid Layout Engine for Visual Calendar
    days_per_row = 7
    for i in range(0, len(date_range), days_per_row):
        row_dates = date_range[i:i+days_per_row]
        cols = st.columns(len(row_dates))
        
        for idx, d in enumerate(row_dates):
            with cols[idx]:
                is_booked = False
                guest_label = ""
                
                for _, row in st.session_state.bookings.iterrows():
                    # If target date falls within an overnight stay slot
                    if row['Check-In'] <= d < row['Check-Out']:
                        is_booked = True
                        guest_label = row['Guest Name']
                        break
                
                # Apply high-contrast visual styling cards
                day_str = d.strftime("%a %d\\n%b")
                if is_booked:
                    st.markdown(
                        f'''<div style="background-color: #FF4B4B; color: white; padding: 10px; 
                        border-radius: 6px; text-align: center; margin-bottom: 10px; min-height: 85px; box-shadow: 1px 1px 3px rgba(0,0,0,0.15)">
                        <strong>{day_str}</strong><br><span style="font-size: 0.75rem; font-weight: bold;">🔴 {guest_label}</span></div>''', 
                        unsafe_html=True
                    )
                else:
                    import datetime
import calendar
import streamlit as st

# Assuming you have your start view date from your widget (e.g., October 2026)
# Replace these with your actual widget variables if they are named differently:
start_date = datetime.date(2026, 10, 1)  
year = start_date.year
month = start_date.month

st.write(f"### 📅 {calendar.month_name[month]} {year}")

# Get the matrix of weeks for the month
cal = calendar.monthcalendar(year, month)

# Create 7 columns for the days of the week headers
days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
cols = st.columns(7)
for i, day_name in enumerate(days_of_week):
    cols[i].markdown(f"<p style='text-align:center; font-weight:bold; color:#888;'>{day_name}</p>", unsafe_allow_html=True)

# Loop through each week and render the days
for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            # Empty space for days belonging to the previous/next month alignment
            cols[i].write("")
        else:
            # --- CUSTOMIZE YOUR BACKEND LOGIC HERE ---
            # Define if this specific date is booked or available
            current_date = datetime.date(year, month, day)
            is_available = True  # Replace with your booking check function (e.g., check_availability(current_date))
            
            # Styling decisions based on availability
            bg_color = "#28A745" if is_available else "#DC3545"
            status_text = "Available" if is_available else "Booked"
            
            # Render the friendly calendar cell
            cols[i].markdown(
                f'''<div style="
                    background-color: {bg_color}; 
                    color: white; 
                    padding: 8px; 
                    border-radius: 6px; 
                    text-align: center; 
                    margin-bottom: 8px;
                    min-height: 70px;
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                ">
                    <span style="font-size: 14px; font-weight: bold; display: block;">{day}</span>
                    <span style="font-size: 11px; opacity: 0.9;">{status_text}</span>
                </div>''', 
                unsafe_allow_html=True
            )

                    
    # Expandable Summary Area
    st.markdown("---")
    st.subheader("🔎 Expandable Guest Reservation Register")
    
    if st.session_state.bookings.empty:
        st.info("No active reservations logged in the framework yet.")
    else:
        for idx, row in st.session_state.bookings.iterrows():
            with st.expander(f"📖 Booking: {row['Guest Name']} ({row['Check-In']} to {row['Check-Out']})"):
                det1, det2 = st.columns(2)
                with det1:
                    st.markdown(f"**👤 Guest Name:** {row['Guest Name']}")
                    st.markdown(f"**📅 Check-In Date:** {row['Check-In']}")
                    st.markdown(f"**📅 Check-Out Date:** {row['Check-Out']}")
                    st.markdown(f"**✉️ Contact Email:** {row['Email']}")
                    st.markdown(f"**📞 Phone Hook:** {row['Phone'] if pd.notna(row['Phone']) and row['Phone'] != '' else 'None Provided'}")
                with det2:
                    st.markdown(f"**🛫 Arrival Flight Stream:** {row['Arrival Flight'] if pd.notna(row['Arrival Flight']) and row['Arrival Flight'] != '' else 'None Linked'}")
                    st.markdown(f"**🛬 Return Flight Stream:** {row['Return Flight'] if pd.notna(row['Return Flight']) and row['Return Flight'] != '' else 'None Linked'}")
                    st.markdown(f"**📝 Trip Notes:** {row['Notes'] if pd.notna(row['Notes']) and row['Notes'] != '' else 'None'}")
                
                # Option to clear records
                act_col1, act_col2 = st.columns([6, 1])
                with act_col2:
                    if st.button("Cancel Booking", key=f"del_{row['Booking ID']}", type="primary"):
                        st.session_state.bookings = st.session_state.bookings[st.session_state.bookings['Booking ID'] != row['Booking ID']]
                        save_bookings(st.session_state.bookings)
                        st.toast("Booking removed successfully!")
                        st.rerun()

    # Outbox Simulation Monitoring Block
    if st.session_state.logs:
        st.markdown("---")
        with st.expander("✉️ System Confirmation Outbox Logs (Simulated)"):
            for log in reversed(st.session_state.logs):
                st.code(log, language="text")

# --- PAGE 2: NEW BOOKING REQUEST ---
elif page == "➕ New Booking Request":
    st.title("➕ Create New Lodging Reservation")
    st.markdown("Fill out the parameters below to verify dates and dispatch a travel receipt simulation email.")
    
    with st.form("booking_form", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            guest_name = st.text_input("Name of Guest *")
            check_in = st.date_input("Check-In Date", datetime.today().date() + timedelta(days=1))
            email = st.text_input("Email Input Address *")
            arrival_flight = st.text_input("Arrival Flight Info / Reference (Optional)")
        with col_f2:
            phone = st.text_input("Phone Input (Optional)")
            check_out = st.date_input("Check-Out Date", datetime.today().date() + timedelta(days=5))
            return_flight = st.text_input("Return Flight Info / Reference (Optional)")
            
        notes = st.text_area("Notes & Special Requests")
        
        submit_btn = st.form_submit_button("Lock & Commit Reservation", type="primary")
        
        if submit_btn:
            if not guest_name or not email:
                st.error("Operational constraint failed: Guest Name and Email input are mandatory metrics.")
            elif check_in >= check_out:
                st.error("Data validation failure: Check-In date must fall strictly before Check-Out date.")
            else:
                # Core Engine Validation Process
                has_overlap, conflict_list = check_overlap(check_in, check_out)      
if has_overlap:
    pass

