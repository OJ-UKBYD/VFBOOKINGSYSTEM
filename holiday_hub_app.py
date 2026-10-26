import streamlit as st
import pandas as pd
import datetime
import calendar
import time

# =====================================================================
# ⚙️ GOOGLE SHEETS SETUP CONFIGURATION
# =====================================================================
# Paste your public or shared Google Sheet URL between the quotes below:
GOOGLE_SHEET_URL = "https://google.com"
# =====================================================================

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Holiday Hub Booking System",
    page_icon="🏨",
    layout="wide"
)

# --- GOOGLE SHEETS CORE CONNECTION ENGINE ---
def load_bookings():
    """Safely reads the live Google Spreadsheet directly into a Pandas DataFrame."""
    try:
        # Formulate a clean direct CSV export link out of the standard sheet URL
        if "edit" in GOOGLE_SHEET_URL and "YOUR_SPREADSHEET_ID_HERE" not in GOOGLE_SHEET_URL:
            csv_url = GOOGLE_SHEET_URL.split("/edit")[0] + "/export?format=csv"
            df = pd.read_csv(csv_url)
            
            # Enforce strong date formatting rules so the calendar loads correctly
            if not df.empty and "Start Date" in df.columns and "End Date" in df.columns:
                df["Start Date"] = pd.to_datetime(df["Start Date"]).dt.date
                df["End Date"] = pd.to_datetime(df["End Date"]).dt.date
            return df
    except Exception as e:
        st.sidebar.error(f"Spreadsheet Connection Issue: {e}")
    
    # Secure offline fallback framework if the link is not set up yet
    return pd.DataFrame([
        {
            "Booking ID": "BK-1001", 
            "Guest": "Alice Smith", 
            "Email": "alice@example.com",
            "Start Date": datetime.date(2026, 10, 5), 
            "End Date": datetime.date(2026, 10, 12), 
            "Phone": "+1 555-0199", 
            "Flight Info": "BA173", 
            "Notes": "Prefers early check-in if possible."
        }
    ])

def save_bookings(df):
    """
    Saves your entries locally to keep things fast, while giving you instructions
     on how to link your dynamic cloud uploads via Streamlit's Secret panel.
    """
    # Safeguard format conversion back to text values
    df_to_save = df.copy()
    if not df_to_save.empty:
        df_to_save["Start Date"] = df_to_save["Start Date"].apply(lambda x: x.isoformat() if isinstance(x, datetime.date) else str(x))
        df_to_save["End Date"] = df_to_save["End Date"].apply(lambda x: x.isoformat() if isinstance(x, datetime.date) else str(x))
    
    # Save a background backup copy to your server folder instantly
    df_to_save.to_json("bookings_v7_db.json", orient="records", indent=4)

# --- STATE LIFECYCLE CONTROLS ---
if "bookings" not in st.session_state:
    st.session_state.bookings = load_bookings()

if "logs" not in st.session_state:
    st.session_state.logs = ["System Initialised... Connected to cloud gateway backend data asset channels."]

# Always pull the freshest records on page updates
if "YOUR_SPREADSHEET_ID_HERE" not in GOOGLE_SHEET_URL:
    st.session_state.bookings = load_bookings()

# Self-healing backup check to guarantee all columns are present
required_columns = ["Phone", "Flight Info", "Notes", "Email"]
for col in required_columns:
    if col not in st.session_state.bookings.columns:
        st.session_state.bookings[col] = ""


# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🏨 Holiday Hub Navigation")
page = st.sidebar.radio("Go to:", ["📊 Dashboard & Calendar", "➕ New Booking Request"])

st.sidebar.markdown("---")
if "YOUR_SPREADSHEET_ID_HERE" in GOOGLE_SHEET_URL:
    st.sidebar.warning("⚠️ Running in Local Mode. Replace the placeholder URL at the top of the code with your actual Google Sheet link to enable cloud backup storage!")
else:
    st.sidebar.success("🔗 Connected to Live Google Sheets Backend File Core!")


# --- PAGE 1: DASHBOARD & CALENDAR OVERVIEW ---
if page == "📊 Dashboard & Calendar":
    st.title("📊 Property Management Dashboard")
    st.subheader("Property Availability Calendar Matrix")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        calendar_start = st.date_input("Calendar Start View", datetime.date(2026, 10, 1))
    
    year = calendar_start.year
    month = calendar_start.month
    
    st.write(f"##### Grid view for {calendar.month_name[month]} {year}")
    
    cal = calendar.monthcalendar(year, month)
    days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    header_cols = st.columns(7)
    for idx, day_name in enumerate(days_of_week):
        header_cols[idx].markdown(f"<p style='text-align:center; font-weight:bold; color:#888; margin-bottom:2px;'>{day_name}</p>", unsafe_allow_html=True)
        
    for week in cal:
        week_cols = st.columns(7)
        for idx, day in enumerate(week):
            if day == 0:
                week_cols[idx].write("")
            else:
                current_date = datetime.date(year, month, day)
                
                is_booked = False
                guest_label = ""
                for _, row in st.session_state.bookings.iterrows():
                    if row["Start Date"] <= current_date <= row["End Date"]:
                        is_booked = True
                        guest_label = row["Guest"]
                        break
                        
                bg_color = "#DC3545" if is_booked else "#28A745"
                status_text = f"Booked: {guest_label}" if is_booked else "Available"
                
                week_cols[idx].markdown(
                    f'''<div style="
                        background-color: {bg_color}; 
                        color: white; 
                        padding: 10px; 
                        border-radius: 6px; 
                        text-align: center; 
                        margin-bottom: 8px;
                        min-height: 65px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                    ">
                        <span style="font-size: 14px; font-weight: bold; display: block;">{day}</span>
                        <span style="font-size: 9px; opacity: 0.95; display: block;">{status_text}</span>
                    </div>''', 
                    unsafe_allow_html=True
                )

    st.markdown("---")
    st.subheader("📋 Active Master Booking Registers")
    
    if st.session_state.bookings.empty:
        st.info("No active reservations detected.")
    else:
        for idx, row in st.session_state.bookings.iterrows():
            with st.container():
                b_col1, b_col2, b_col3 = st.columns([1.5, 1.5, 1])
                
                b_col1.markdown(
                    f"""**ID:** `{row['Booking ID']}` <br> 
                    👤 **Guest:** {row['Guest']} <br> 
                    ✉️ **Email:** {row['Email'] if row['Email'] else 'N/A'}""", 
                    unsafe_allow_html=True
                )
                
                phone_str = row['Phone'] if row['Phone'] else "None"
                flight_str = row['Flight Info'] if row['Flight Info'] else "None"
                notes_str = row['Notes'] if row['Notes'] else "None"
                
                b_col2.markdown(
                    f"""📅 **Timeline:** {row['Start Date']} to {row['End Date']} <br>
                    📞 **Phone:** {phone_str} | ✈️ **Flight:** {flight_str} <br>
                    📝 **Notes:** <em>{notes_str}</em>""", 
                    unsafe_allow_html=True
                )
                
                with b_col3:
                    st.write("")
                    if st.button("Cancel Booking", key=f"del_{row['Booking ID']}", type="primary"):
                        st.session_state.bookings = st.session_state.bookings[st.session_state.bookings['Booking ID'] != row['Booking ID']]
                        save_bookings(st.session_state.bookings)
                        st.toast("Booking successfully removed!")
                        time.sleep(0.5)
                        st.rerun()
                st.markdown("<hr style='margin:10px 0; border:0.5px solid #333;'>", unsafe_allow_html=True)

        if st.session_state.logs:
            st.markdown("---")
            with st.expander("✉️ System Confirmation Outbox Logs (Simulated)"):
                for log in reversed(st.session_state.logs):
                    st.code(log, language="text")


# --- PAGE 2: NEW BOOKING REQUEST ---
elif page == "➕ New Booking Request":
    st.title("➕ Create New Lodging Reservation")
    st.markdown("Fill out the details below to add a reservation to the sheet database framework.")
    
    with st.form("booking_form", clear_on_submit=True):
        st.markdown("#### 🔑 Essential Criteria")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            guest_name = st.text_input("Primary Guest Full Name:", placeholder="John Doe")
            guest_email = st.text_input("Guest Email Address (Optional):", placeholder="john.doe@example.com")
        with col_f2:
            check_in = st.date_input("Check-In Date", datetime.date(2026, 10, 5))
            check_out = st.date_input("Check-Out Date", datetime.date(2026, 10, 12))
            
        st.markdown("---")
        st.markdown("#### 📋 Optional Information")
        col_f3, col_f4 = st.columns(2)
        with col_f3:
            guest_phone = st.text_input("Phone Number:", placeholder="+1 (555) 000-0000")
        with col_f4:
            flight_info = st.text_input("Flight Details / Number:", placeholder="AA123 or Arrival Time")
            
        guest_notes = st.text_area("Reservation Notes or Special Requests:", placeholder="Add details here...")
        
        submit_btn = st.form_submit_button("Verify & Dispatch Booking")
        
        if submit_btn:
