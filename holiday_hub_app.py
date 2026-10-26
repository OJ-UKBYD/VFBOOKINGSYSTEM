import streamlit as st
import pandas as pd
import datetime
import calendar
import json
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Holiday Hub Booking System",
    page_icon="🏨",
    layout="wide"
)

# --- DATABASE / DATA PERSISTENCE SIMULATION ---
DB_FILE = "bookings_db.json"

def load_bookings():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                return pd.DataFrame(data)
        except:
            pass
    # Default mock data if database file doesn't exist yet
    return pd.DataFrame([
        {"Booking ID": "BK-1001", "Property": "Ocean View Villa", "Start Date": "2026-10-05", "End Date": "2026-10-12", "Guest": "Alice Smith"},
        {"Booking ID": "BK-1002", "Property": "Mountain Timber Cabin", "Start Date": "2026-10-15", "End Date": "2026-10-20", "Guest": "Bob Jones"}
    ])

def save_bookings(df):
    df.to_json(DB_FILE, orient="records", indent=4)

# --- STATE MANAGEMENT ---
if "bookings" not in st.session_state:
    st.session_state.bookings = load_bookings()

if "logs" not in st.session_state:
    st.session_state.logs = ["System Initialized... Waiting for reservation inputs."]

# Convert dates to string format objects cleanly for comparisons
st.session_state.bookings["Start Date"] = pd.to_datetime(st.session_state.bookings["Start Date"]).dt.date
st.session_state.bookings["End Date"] = pd.to_datetime(st.session_state.bookings["End Date"]).dt.date


# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🏨 Holiday Hub Navigation")
page = st.sidebar.radio("Go to:", ["📊 Dashboard & Calendar", "➕ New Booking Request"])

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Adjust your variables or properties inside the forms to test the overlap checker simulation live.")


# --- PAGE 1: DASHBOARD & CALENDAR MATRIX ---
if page == "📊 Dashboard & Calendar":
    st.title("📊 Property Management Dashboard")
    st.subheader("Property Availability Calendar Matrix")
    
    # Calendar inputs
    col_c1, col_c2 = st.columns([1, 2])
    with col_c1:
        calendar_start = st.date_input("Calendar Start View", datetime.date(2026, 10, 1))
    
    # Filter selection by property
    properties_list = ["Ocean View Villa", "Mountain Timber Cabin", "Cozy Downtown Loft"]
    selected_property = st.sidebar.selectbox("Filter Calendar Matrix By Property:", properties_list)
    
    st.markdown(f"#### 📅 Showing Availability for: **{selected_property}**")
    
    # Build a friendly month-by-month grid layout
    year = calendar_start.year
    month = calendar_start.month
    
    st.write(f"##### Row view for {calendar.month_name[month]} {year}")
    
    # Calendar configuration structure matrix
    cal = calendar.monthcalendar(year, month)
    days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    # Headers
    header_cols = st.columns(7)
    for idx, day_name in enumerate(days_of_week):
        header_cols[idx].markdown(f"<p style='text-align:center; font-weight:bold; color:#888; margin-bottom:2px;'>{day_name}</p>", unsafe_allow_html=True)
        
    # Weeks iterator loop structure
    for week in cal:
        week_cols = st.columns(7)
        for idx, day in enumerate(week):
            if day == 0:
                week_cols[idx].write("")
            else:
                current_date = datetime.date(year, month, day)
                
                # Check real database list array records for overlaps
                property_filter = st.session_state.bookings[st.session_state.bookings["Property"] == selected_property]
                
                is_booked = False
                for _, row in property_filter.iterrows():
                    if row["Start Date"] <= current_date <= row["End Date"]:
                        is_booked = True
                        break
                        
                # UI Customizer Styling decisions based on availability flags 
                bg_color = "#DC3545" if is_booked else "#28A745"
                status_text = "Booked" if is_booked else "Available"
                
                week_cols[idx].markdown(
                    f'''<div style="
                        background-color: {bg_color}; 
                        color: white; 
                        padding: 10px; 
                        border-radius: 6px; 
                        text-align: center; 
                        margin-bottom: 8px;
                        min-height: 65px;
                    ">
                        <span style="font-size: 14px; font-weight: bold; display: block;">{day}</span>
                        <span style="font-size: 10px; opacity: 0.9;">{status_text}</span>
                    </div>''', 
                    unsafe_allow_html=True
                )

    # --- RENDER EXISTENT BOOKINGS LIST MANAGEMENT ---
    st.markdown("---")
    st.subheader("📋 Active Master Booking Registers")
    
    if st.session_state.bookings.empty:
        st.info("No active reservations detected.")
    else:
        for idx, row in st.session_state.bookings.iterrows():
            with st.container():
                b_col1, b_col2, b_col3 = st.columns([2, 3, 2])
                b_col1.markdown(f"**ID:** `{row['Booking ID']}` <br> **Guest:** {row['Guest']}", unsafe_allow_html=True)
                b_col2.markdown(f"🏠 **{row['Property']}** <br> 📅 {row['Start Date']} to {row['End Date']}", unsafe_allow_html=True)
                
                with b_col3:
                    # Clean separation spacing container fix
                    st.write("")
                    act_col1, act_col2 = st.columns(2)
                    with act_col1:
                        pass # Space holder
                    with act_col2:
                        if st.button("Cancel", key=f"del_{row['Booking ID']}", type="primary"):
                            st.session_state.bookings = st.session_state.bookings[st.session_state.bookings['Booking ID'] != row['Booking ID']]
                            save_bookings(st.session_state.bookings)
                            st.toast("Booking removed successfully!")
                            st.rerun()
                st.markdown("<hr style='margin:10px 0; border:0.5px solid #333;'>", unsafe_allow_html=True)

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
            guest_name = st.text_input("Primary Guest Full Name:", placeholder="John Doe")
            chosen_property = st.selectbox("Select Target Property Structure:", ["Ocean View Villa", "Mountain Timber Cabin", "Cozy Downtown Loft"])
        with col_f2:
            check_in = st.date_input("Check-In Date", datetime.date(2026, 10, 5))
            check_out = st.date_input("Check-Out Date", datetime.date(2026, 10, 12))
            
        submit_btn = st.form_submit_button("Verify & Dispatch Booking")
        
        if submit_btn:
            if not guest_name:
                st.error("Please provide a guest name.")
            elif check_in >= check_out:
                st.error("Error: Check-Out Date must fall cleanly after your chosen Check-In Date.")
            else:
                # Calculate real overlap logic parameter checker safely here
                property_bookings = st.session_state.bookings[st.session_state.bookings["Property"] == chosen_property]
                
                has_overlap = False
                for _, res in property_bookings.iterrows():
                    # If the ranges intersect: (StartA <= EndB) and (EndA >= StartB)
                    if (check_in <= res["End Date"]) and (check_out >= res["Start Date"]):
                        has_overlap = True
                        break
                
                if has_overlap:
                    st.error(f"❌ Date Conflict: '{chosen_property}' is already reserved during those dates. Check the dashboard grid matrix.")
                else:
                    # Successfully process allocation write row append
                    new_id = f"BK-{len(st.session_state.bookings) + 1001}"
                    new_record = {
                        "Booking ID": new_id,
                        "Property": chosen_property,
                        "Start Date": check_in,
                        "End Date": check_out,
                        "Guest": guest_name
                    }
                    
                    # Concat record to current storage architecture frame
                    st.session_state.bookings = pd.concat([st.session_state.bookings, pd.DataFrame([new_record])], ignore_index=True)
                    save_bookings(st.session_state.bookings)
                    
                    # Generate dynamic system string logger receipt log output array simulation
                    log_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    simulated_log = f"[{log_timestamp}] EMAIL DISPATCHED to bookings@holidayhub.com\nSubject: Confirmation Receipt {new_id}\nGuest: {guest_name}\nProperty: {chosen_property}\nPeriod: {check_in} -> {check_out}\nStatus: System Confirmed Safe Allocation Matrix Checked."
                    st.session_state.logs.append(simulated_log)
                    
                    # Clean markdown layout notice verification execution block
                    st.markdown()
